"""Fixed Remix provider choices coexist with endless, procedural levels."""
from dataclasses import replace
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from system_panic.model import Controls, FIXED_DT
from system_panic.paks import CHANNELS, get_catalog
from system_panic.paks.registry import Catalog
from system_panic.preferences import Preferences
from system_panic.world import World


class StaticRemixTests(unittest.TestCase):
    def setUp(self):
        self.catalog = get_catalog()
        self.mix = {channel: self.catalog.providers(channel)[index]
                    for index, channel in enumerate(CHANNELS)}
        self.worlds = []

    def world(self, prefs=None, **kwargs):
        world = World(prefs or Preferences(), seed=24, **kwargs)
        self.worlds.append(world)
        return world

    def tearDown(self):
        for world in self.worlds:
            world.close()

    def test_exact_selection_ignores_shuffle_preferences_and_copies_the_draft(self):
        prefs = Preferences(enabled=[self.catalog.paks[-1].id])
        original = self.mix.copy()
        with patch.object(World, "choose", side_effect=AssertionError("Fixed mixes cannot roll providers")):
            world = self.world(prefs, fixed_mix=self.mix)
        self.assertEqual(world.mix, original)
        self.assertEqual(world.fixed_mix, original)
        self.assertFalse(world.can_shuffle)
        for channel in CHANNELS:
            self.assertEqual(type(world.component(channel)),
                             self.catalog.by_id[original[channel]].parts[channel].implementation)
        self.mix["pilot"] = self.catalog.paks[-1].id
        self.assertEqual(world.mix, original)
        self.assertEqual(world.fixed_mix, original)
        self.assertEqual(prefs.enabled, [self.catalog.paks[-1].id])

    def test_timer_and_explicit_shuffle_leave_state_and_components_intact(self):
        world = self.world(fixed_mix=self.mix)
        world.phase = "active"
        world.shuffle_timer = -1
        world.player.invulnerable = 60
        parts = world._parts.copy()
        world.step(FIXED_DT, Controls())
        self.assertGreater(world.time, 0)
        self.assertEqual(world.mix, self.mix)
        self.assertEqual(world.shuffle_count, 0)
        self.assertEqual(world.transition, 0)
        before = (world.rng.getstate(), world.player.pos.copy(), world.time,
                  world.projectiles.copy(), world.shuffle_timer, world.events.copy())
        for _ in range(3):
            world.shuffle()
        self.assertEqual((world.rng.getstate(), world.player.pos, world.time,
                          world.projectiles, world.shuffle_timer, world.events), before)
        self.assertEqual(world._parts, parts)
        self.assertEqual(world.shuffle_count, 0)
        self.assertEqual(world.transition, 0)

    def test_level_arrival_regenerates_layout_without_changing_providers(self):
        world = self.world(fixed_mix=self.mix)
        old_cover = world.cover.copy()
        signature = tuple(tuple(wall.rect) for wall in world.cover)
        part = world.component("obstacles")
        for wall in world.cover:
            wall.health = 0
        world.enemies.clear()
        world.phase = "clear"
        world.phase_timer = 0
        world.step(FIXED_DT, Controls())
        self.assertEqual((world.wave, world.phase, world.transition), (2, "active", 0))
        self.assertEqual(world.mix, self.mix)
        self.assertIs(world.component("obstacles"), part)
        self.assertEqual(len(world.enemies), 2)
        self.assertNotEqual(tuple(tuple(wall.rect) for wall in world.cover), signature)
        self.assertTrue(all(wall.health == wall.max_health > 0 for wall in world.cover))
        self.assertTrue(all(wall is not old for wall in world.cover for old in old_cover))
        world.enemies.clear()
        world.wave = 100
        world.phase, world.phase_timer = "clear", 0
        world.step(FIXED_DT, Controls())
        self.assertEqual((world.wave, len(world.enemies)), (101, 101))
        self.assertEqual(world.mix, self.mix)

    def test_six_complementary_partial_paks_can_form_a_fixed_remix(self):
        base = self.catalog.paks[0]
        paks = tuple(replace(base, id="partial_" + channel, parts={channel: base.parts[channel]})
                     for channel in CHANNELS)
        catalog = Catalog(paks, (), ())
        mix = {channel: "partial_" + channel for channel in CHANNELS}
        world = self.world(catalog=catalog, fixed_mix=mix)
        self.assertFalse(catalog.complete_ids())
        self.assertEqual(world.mix, mix)
        self.assertEqual(len(world.enemies), 1)
        self.assertFalse(world.can_shuffle)

    def test_invalid_or_unavailable_mapping_is_rejected_without_fallback(self):
        incomplete = {key: value for key, value in self.mix.items() if key != "pilot"}
        invalid = [incomplete, [], {}, self.mix | {"other": "signal_runner"},
                   self.mix | {"pilot": "not_installed"}, self.mix | {"pilot": 3}]
        for mix in invalid:
            with self.subTest(mix=mix), self.assertRaises(ValueError):
                self.world(fixed_mix=mix)
        base = self.catalog.paks[0]
        only_music = replace(base, parts={"music": base.parts["music"]})
        with self.assertRaises(ValueError):
            self.world(catalog=Catalog((only_music,), (), ()),
                       fixed_mix={channel: base.id for channel in CHANNELS})
        with self.assertRaises(ValueError):
            self.world(solo=base.id, fixed_mix=self.mix)

    def test_existing_solo_and_shuffling_runs_keep_their_selection_rules(self):
        solo = self.world(solo=self.catalog.paks[0].id)
        self.assertIsNone(solo.fixed_mix)
        self.assertFalse(solo.can_shuffle)
        self.assertEqual(set(solo.mix.values()), {self.catalog.paks[0].id})
        prefs = Preferences(enabled=[pak.id for pak in self.catalog.paks[:2]])
        world = self.world(prefs)
        self.assertIsNone(world.fixed_mix)
        self.assertTrue(world.can_shuffle)
        old = world.mix.copy()
        world.shuffle()
        self.assertNotEqual(world.mix, old)
        self.assertEqual(world.shuffle_count, 1)
        self.assertGreater(world.transition, 0)


if __name__ == "__main__":
    unittest.main()
