"""Performance interruption, durable exact exclusions and bounded shuffle recovery."""
from dataclasses import replace
import itertools
import json
import os
from pathlib import Path
import random
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pygame
from system_panic.app import App
from system_panic.combinations import CombinationHistory, CombinationSpace, NoAvailableCombination, PerformanceWatch, mix_key
from system_panic.input_devices import A, B, PadFrame, spatial_focus
from system_panic.model import Controls
from system_panic.paks import CHANNELS, Catalog, get_catalog
from system_panic.preferences import Preferences
from system_panic.remixes import Remix
from system_panic.world import World

TEMP = ROOT / "output/test-temp"
TEMP.mkdir(parents=True, exist_ok=True)


def uniform(provider):
    return dict.fromkeys(CHANNELS, provider)


class PerformanceWatchTests(unittest.TestCase):
    def test_strict_threshold_and_recovery_reset(self):
        watch = PerformanceWatch()
        for _ in range(4):
            self.assertFalse(watch.observe(.25, "same"))
        self.assertTrue(watch.observe(.25, "same"))
        self.assertEqual(watch.slow_fps, 4)
        self.assertFalse(watch.observe(.1, "same"))
        self.assertEqual(watch.seconds, 0)
        for _ in range(9):
            self.assertFalse(watch.observe(.1, "same"))

    def test_interrupted_contexts_and_invalid_time_do_not_accumulate(self):
        watch = PerformanceWatch()
        for context in ("old", "new", None, "new", None):
            self.assertFalse(watch.observe(.6, context))
        for elapsed in (0, -1, float("nan"), float("inf")):
            self.assertFalse(watch.observe(elapsed, "same"))
            self.assertEqual(watch.seconds, 0)


class CombinationSelectionTests(unittest.TestCase):
    def test_only_remaining_combination_is_found_without_retries(self):
        keys = list(itertools.product(("a", "b"), repeat=6))
        space = CombinationSpace([("a", "b")] * 6)
        for remaining in keys:
            excluded = set(keys) - {remaining}
            for seed in (0, 24, 91):
                self.assertEqual(mix_key(space.pick(random.Random(seed), excluded)), remaining)
            self.assertEqual(space.available(excluded), 1)
        self.assertIsNone(space.pick(random.Random(24), set(keys)))

    def test_partial_provider_spaces(self):
        pools = [["pilot"], ["enemy"], ["first", "second"], ["music"], ["background"], ["obstacles"]]
        space = CombinationSpace(pools)
        first = tuple(pool[0] for pool in pools)
        self.assertEqual(space.available({first}), 1)
        self.assertEqual(space.pick(random.Random(0), {first})["weapon"], "second")

    def test_large_space_uses_one_bounded_rng_draw(self):
        space = CombinationSpace([list(map(str, range(100)))] * 6)
        rng = SimpleNamespace(randrange=lambda count: count - 1)
        blocked = {tuple(["99"] * 6)}
        self.assertEqual(space.total, 10 ** 12)
        self.assertEqual(mix_key(space.pick(rng, blocked)), ("99", "99", "99", "99", "99", "98"))

    def test_world_initial_periodic_and_recovery_exclude_exact_matches(self):
        catalog = get_catalog()
        providers = ["signal_runner", "phase_garden"]
        prefs = Preferences(enabled=providers)
        all_keys = set(itertools.product(providers, repeat=6))
        survivor = ("signal_runner",) * 5 + ("phase_garden",)
        world = World(prefs, 24, blocked_mixes=all_keys - {survivor})
        try:
            self.assertEqual(mix_key(world.mix), survivor)
            self.assertFalse(world.can_shuffle)
            # Leave exactly one alternate which retains five old channels.
            alternate = ("phase_garden",) + survivor[1:]
            world.blocked_mixes.remove(alternate)
            world.blocked_mixes.add(survivor)
            self.assertTrue(world.can_shuffle)
            world.phase, world.shuffle_timer = "active", 0
            world.step(1 / 120, Controls())
            self.assertEqual(world.shuffle_count, 1)
            self.assertEqual(mix_key(world.mix), alternate)
        finally:
            world.close()
        with self.assertRaises(NoAvailableCombination):
            World(prefs, catalog=catalog, blocked_mixes=all_keys)

    def test_locks_solo_and_fixed_selection_respected(self):
        blocked = {mix_key(uniform("signal_runner"))}
        with self.assertRaises(NoAvailableCombination):
            World(Preferences(), solo="signal_runner", blocked_mixes=blocked)
        with self.assertRaises(NoAvailableCombination):
            World(Preferences(), fixed_mix=uniform("signal_runner"), blocked_mixes=blocked)
        world = World(Preferences(enabled=["signal_runner", "phase_garden"]), blocked_mixes=blocked)
        self.assertNotIn(mix_key(world.mix), blocked)
        self.assertTrue(world.can_shuffle)
        world.close()
        world = World(Preferences(enabled=["signal_runner", "phase_garden"], shuffle_channels=["weapon"]), seed=9)
        try:
            original = world.mix.copy()
            world.blocked_mixes.add(mix_key(original))
            world.shuffle()
            self.assertNotEqual(world.mix["weapon"], original["weapon"])
            self.assertEqual({k: v for k, v in world.mix.items() if k != "weapon"},
                             {k: v for k, v in original.items() if k != "weapon"})
            world.prefs.shuffle_channels = []
            self.assertFalse(world.can_shuffle)
        finally:
            world.close()

    def test_complementary_partial_paks_use_only_eligible_providers(self):
        base = get_catalog().paks[0]
        partials = [replace(base, id="partial_" + channel, parts={channel: base.parts[channel]}) for channel in CHANNELS]
        weapon = replace(partials[2], id="other_weapon")
        catalog = Catalog(tuple([*partials, weapon]), (), ())
        blocked_mix = {channel: "partial_" + channel for channel in CHANNELS}
        blocked = {mix_key(blocked_mix)}
        world = World(Preferences(enabled=list(catalog.by_id)), catalog=catalog, blocked_mixes=blocked)
        self.assertEqual(world.mix, blocked_mix | {"weapon": "other_weapon"})
        world.close()


class CombinationHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEMP)
        self.directory = Path(self.temp.name)
        self.history = CombinationHistory(self.directory)

    def tearDown(self):
        self.temp.cleanup()

    def test_round_trip_deduplication_and_uninstalled_providers_retained(self):
        mix = uniform("uninstalled_provider")
        self.assertTrue(self.history.flag(mix, 7.5, 1.2))
        mix["pilot"] = "changed"
        self.history.flag(uniform("uninstalled_provider"), 3, 4)
        loaded = CombinationHistory(self.directory)
        self.assertEqual(len(loaded.entries), 1)
        self.assertEqual(loaded.entries[0].mix, uniform("uninstalled_provider"))
        self.assertEqual(loaded.entries[0].fps, 7.5)
        self.assertTrue(loaded.remove(mix_key(loaded.entries[0].mix)))
        self.assertFalse(CombinationHistory(self.directory).keys)

    def test_failed_flag_still_blocks_in_memory_and_failed_removal_preserves_disk(self):
        first, second = uniform("first"), uniform("second")
        self.history.flag(first, 8, 1.25)
        before = self.history.path.read_bytes()
        with patch.object(Path, "replace", side_effect=OSError("read only")):
            self.assertFalse(self.history.flag(second, 6, 1.5))
            self.assertTrue(self.history.dirty)
            self.assertIn(mix_key(second), self.history.keys)
            self.assertEqual(self.history.path.read_bytes(), before)
            self.assertFalse(self.history.remove(mix_key(first)))
            self.assertIn(mix_key(first), self.history.keys)
        self.assertFalse(list(self.directory.glob("*.tmp")))
        self.assertTrue(self.history.retry())
        self.assertEqual(CombinationHistory(self.directory).keys, {mix_key(first), mix_key(second)})

    def test_corruption_and_invalid_records_are_reported_without_repairing_mix(self):
        self.history.flag(uniform("valid"), 8, 1.2)
        payload = json.loads(self.history.path.read_text())
        valid = payload["combinations"][0]
        payload["combinations"] += [valid, valid | {"mix": {}}, valid | {"fps": True}, valid | {"seconds": -1},
                                     valid | {"fps": float("nan")}, valid | {"detected_at": "invalid"}]
        self.history.path.write_text(json.dumps(payload))
        loaded = CombinationHistory(self.directory)
        self.assertEqual(len(loaded.entries), 1)
        self.assertIn("Skipped 5", loaded.error)
        self.history.path.write_text("{")
        loaded = CombinationHistory(self.directory)
        self.assertFalse(loaded.keys)
        self.assertIn("Could not read", loaded.error)


class CombinationUITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEMP)
        self.directory = Path(self.temp.name)
        self.app = App(self.directory, seed=24)

    def tearDown(self):
        self.app.quit()
        pygame.quit()
        self.temp.cleanup()

    def click(self, identifier):
        self.app.draw()
        button = next(b for b in self.app.buttons if b.id == identifier)
        target = self.app.presentation_rect()
        pos = (target.x + button.rect.centerx * target.width / 1280,
               target.y + button.rect.centery * target.height / 800)
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))

    def active(self, **kwargs):
        self.app.start(**kwargs)
        self.app.world.phase = "active"
        self.app.world.player.invulnerable = 100
        return self.app.world

    def detect(self):
        context = self.app.performance_context()
        for _ in range(5):
            self.app.check_performance(.25, context)

    def test_detect_freezes_lists_all_components_persists_and_recovers_same_run(self):
        world = self.active()
        world.score, world.kills, world.wave, world.powerups_collected = 1234, 7, 4, 3
        mix = world.mix.copy()
        self.detect()
        self.assertEqual(self.app.route, "performance")
        self.assertIn(mix_key(mix), CombinationHistory(self.directory).keys)
        before = (world.time, world.player.pos.copy(), world.rng.getstate(), world.shuffle_timer)
        self.app.update(4, Controls(fire=True))
        self.assertEqual((world.time, world.player.pos, world.rng.getstate(), world.shuffle_timer), before)
        with patch("system_panic.graphics.Graphics.text", wraps=self.app.graphics.text) as draw_text:
            self.app.draw()
        texts = [str(call.args[1]) for call in draw_text.call_args_list]
        for channel in CHANNELS:
            self.assertIn(channel.upper(), texts)
            self.assertIn(self.app.catalog.by_id[mix[channel]].name, texts)
        self.click("performance-continue")
        self.assertEqual(self.app.route, "game")
        self.assertIs(self.app.world, world)
        self.assertNotEqual(world.mix, mix)
        self.assertEqual((world.score, world.kills, world.wave, world.powerups_collected), (1234, 7, 4, 3))
        self.assertEqual(world.transition, 0)
        self.assertEqual(self.app.performance_watch.seconds, 0)
        time = world.time
        self.app.update(1 / 60, Controls())
        self.assertGreater(world.time, time)

    def test_remix_solo_and_locked_exhaustion_go_home(self):
        for kwargs in ({"fixed_mix": uniform("signal_runner")}, {"solo": "phase_garden"}, {}):
            self.app.prefs.shuffle_channels = []
            world = self.active(**kwargs)
            self.detect()
            self.app.draw()
            self.assertNotIn("performance-continue", [b.id for b in self.app.buttons])
            self.click("performance-home")
            self.assertEqual(self.app.route, "home")
            self.assertIsNone(self.app.world)
            self.assertFalse(world._parts)

    def test_explicit_menu_escape_and_controller_back_never_resume_failed_mix(self):
        for method in ("button", "escape", "controller"):
            self.active()
            self.detect()
            if method == "button":
                self.click("performance-home")
            elif method == "escape":
                self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0))
            else:
                self.app.pad_input(PadFrame(pressed=frozenset({B})), .016)
            self.assertEqual(self.app.route, "home")
            self.assertIsNone(self.app.world)

    def test_non_gameplay_intervals_and_changed_mix_do_not_trigger(self):
        world = self.active()
        context = self.app.performance_context()
        self.app.check_performance(.75, context)
        self.app.navigate("pause")
        self.app.check_performance(20, context)
        self.app.navigate("game")
        self.app.check_performance(.75, context)
        self.assertEqual(self.app.route, "game")
        for attribute, value in (("phase", "ready"), ("phase", "clear"), ("transition", .25)):
            setattr(world, attribute, value)
            self.app.check_performance(20, context)
            setattr(world, attribute, "active" if attribute == "phase" else 0)
        self.app.window_focused = False
        self.app.check_performance(20, context)
        self.app.window_focused = True
        context = self.app.performance_context()
        self.app.check_performance(.75, context)
        world.shuffle()
        world.transition = 0
        self.app.check_performance(.75, context)
        self.assertEqual(self.app.route, "game")

    def test_actual_run_loop_samples_unclamped_presented_frames(self):
        self.active()
        self.app.clock = SimpleNamespace(tick=lambda limit: 125)
        original_draw = self.app.draw
        calls = 0
        def draw():
            nonlocal calls
            calls += 1
            original_draw()
            if self.app.route == "performance" or calls > 14:
                self.app.running = False
        with patch("system_panic.world.World.advance"), patch.object(self.app, "draw", side_effect=draw):
            self.app.run()
        self.assertEqual(self.app.route, "performance")
        self.assertEqual(len(CombinationHistory(self.directory).entries), 1)
        self.assertAlmostEqual(self.app.performance_problem[1], 8)
        # run() releases SDL; restore it for the common cleanup method.
        pygame.init()

    def test_run_loop_excludes_the_frame_that_resumes_from_a_menu(self):
        self.active()
        self.app.navigate("pause")
        timings = iter((16, 2000, 16))
        self.app.clock = SimpleNamespace(tick=lambda limit: next(timings))
        events = iter(([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0)], [], []))
        draw = self.app.draw
        calls = 0
        def bounded_draw():
            nonlocal calls
            calls += 1
            draw()
            if calls == 4:
                self.app.running = False
        with patch("pygame.event.get", side_effect=lambda: next(events)), \
                patch("system_panic.world.World.advance"), patch.object(self.app, "draw", side_effect=bounded_draw):
            self.app.run()
        self.assertEqual(self.app.route, "game")
        self.assertFalse(self.app.combination_history.keys)
        pygame.init()

    def test_settings_management_pagination_remove_failure_and_nested_back(self):
        for index in range(8):
            self.app.combination_history.flag(uniform("provider_" + str(index)), 8, 1.25)
        self.active()
        self.app.navigate("pause")
        self.click("pause-settings")
        self.click("combinations")
        self.click("flagged_page:next")
        self.click("flagged:7")
        selected = self.app.selected_flagged()
        with patch.object(Path, "replace", side_effect=OSError("read only")):
            self.click("flagged-remove")
        self.assertIn(mix_key(selected.mix), self.app.combination_history.keys)
        self.click("flagged-remove")
        self.assertNotIn(mix_key(selected.mix), CombinationHistory(self.directory).keys)
        self.click("back")
        self.assertEqual(self.app.route, "settings")
        self.click("back")
        self.assertEqual(self.app.route, "pause")

    def test_blocked_remix_saved_and_solo_launches_can_be_reenabled(self):
        mix = uniform("signal_runner")
        self.app.combination_history.flag(mix, 8, 1.25)
        self.app.remixes = [Remix("favorite", "Keep me", mix)]
        self.app.open_remix()
        self.app.remix_mix = mix.copy()
        self.app.draw()
        self.assertIn("remix-blocked", [b.id for b in self.app.buttons])
        self.app.play_remix()
        self.assertIsNone(self.app.world)
        self.app.start("signal_runner")
        self.assertIsNone(self.app.world)
        self.app.prefs.enabled = ["signal_runner"]
        self.app.start()
        self.assertIsNone(self.app.world)
        self.click("remix-blocked")
        self.click("flagged-remove")
        self.click("back")
        self.app.play_remix()
        self.assertEqual(self.app.route, "game")
        self.assertEqual(self.app.world.mix, mix)
        self.assertEqual(self.app.remixes[0].name, "Keep me")

    def test_save_failure_dialog_can_retry_and_every_widget_is_reachable(self):
        self.active()
        with patch.object(Path, "replace", side_effect=OSError("read only")):
            self.detect()
        self.assertTrue(self.app.combination_history.dirty)
        for route in ("performance", "settings", "combinations"):
            self.app.route = route
            self.app.draw()
            rects = [button.rect for button in self.app.buttons]
            for rect in rects:
                self.assertTrue(self.app.canvas.get_rect().contains(rect))
            reached, pending = {0}, [0]
            while pending:
                index = pending.pop()
                for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    following = spatial_focus(rects, index, direction)
                    if following not in reached:
                        reached.add(following)
                        pending.append(following)
            self.assertEqual(reached, set(range(len(rects))), route)
        self.app.route = "performance"
        self.click("performance-save")
        self.assertFalse(self.app.combination_history.dirty)
        self.app.input_device = "gamepad"
        self.app.keyboard_focus = False
        self.app.draw()
        self.app.pad_input(PadFrame(pressed=frozenset({A}), activity=True), .016)
        self.assertEqual(self.app.route, "game")
