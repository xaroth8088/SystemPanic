"""Defeat input safety, hull rendering boundaries, and Pak-local time impacts."""
import importlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pygame
from system_panic.app import App, VIEWPORT
from system_panic.input_devices import Gamepads, A, B, START
from system_panic.model import Controls, Vec
from system_panic.run_feedback import desaturate_hull
from tests.test_gamepad import FakeBackend, FakePad


class RunFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT / "output/test-temp")
        self.pad = FakePad()
        self.devices = Gamepads(FakeBackend(self.pad))
        self.app = App(Path(self.temporary.name), 24, gamepads=self.devices)
        self.app.start("echo_vault")
        self.app.world.phase = "active"
        self.app.world.transition = 0.
        self.app.world.cover = []
        self.devices.poll()

    def tearDown(self):
        self.app.quit()
        pygame.quit()
        self.temporary.cleanup()

    def die(self):
        self.app.world.player.health = 0
        self.app.world.score = 8765
        self.app.update(1 / 60, Controls())
        self.assertEqual(self.app.route, "game-over")

    def test_defeat_stops_playback_and_sounds_once_before_modal(self):
        with patch.object(self.app.audio, "play", wraps=self.app.audio.play) as play:
            self.die()
            world = self.app.world
            state = (world.time, world.wave, world.rng.getstate(), world.player.pos.copy())
            world.shake, world.transition = 3., .2
            self.app.draw()
            self.assertFalse(self.app.buttons)
            self.assertIsNone(self.app.audio.current)
            self.assertEqual(self.app.store.load().high_score, 8765)
            self.app.update(.8)
            self.assertEqual(self.app.route, "game-over")
            self.assertAlmostEqual(world.shake, 1.)
            self.assertAlmostEqual(world.transition, .1)
            self.app.update(.6)
            self.assertEqual(self.app.route, "outcome")
            self.assertEqual((world.shake, world.transition), (0., 0.))
            self.assertEqual((world.time, world.wave, world.rng.getstate(), world.player.pos), state)
            self.assertEqual([call.args for call in play.call_args_list].count(("game_over",)), 1)
            self.app.draw()
            self.assertEqual({b.id for b in self.app.buttons}, {"retry", "library"})

    def test_key_mouse_mashing_and_held_controls_cannot_skip_transition(self):
        self.die()
        for key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
            for _ in range(4):
                self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0))
                self.app.update(.2)
                self.assertEqual(self.app.route, "game-over")
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 420)))
        self.app.update(.2)
        self.assertEqual(self.app.route, "game-over")
        with patch("pygame.key.get_pressed", return_value=[True]):
            self.app.update(2)
        with patch("pygame.mouse.get_pressed", return_value=(True, False, False)):
            self.app.update(2)
        self.assertEqual(self.app.route, "game-over")
        self.app.update(.29)
        self.assertEqual(self.app.route, "game-over")
        self.app.update(.02)
        self.assertEqual(self.app.route, "outcome")

    def test_pad_buttons_stick_trigger_and_focus_require_release(self):
        self.pad.buttons = {A}
        self.die()
        self.pad.buttons = {A, B, START}
        for _ in range(3):
            self.app.update(.7)
            self.assertEqual(self.app.route, "game-over")
        self.pad.buttons.clear()
        for axis, value in ((0, 20000), (5, 32767)):
            self.pad.axes = {axis: value}
            self.assertFalse(self.devices.poll().neutral)
            self.app.update(1)
            self.assertEqual(self.app.route, "game-over")
        self.pad.axes.clear()
        self.app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.app.update(2)
        self.assertEqual(self.app.route, "game-over")
        self.app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
        self.app.update(.31)
        self.assertEqual(self.app.route, "outcome")
        self.app.draw()
        self.pad.buttons = {A}
        self.app.update(.02)  # First press is blocked until a neutral outcome frame.
        self.assertEqual(self.app.route, "outcome")
        self.pad.buttons.clear()
        self.app.update(.02)
        self.pad.buttons = {A}
        self.app.update(.02)
        self.assertEqual((self.app.route, self.app.world.solo), ("game", "echo_vault"))

    def test_hull_blends_linearly_and_keeps_hud_in_color(self):
        surface = pygame.Surface((1, 1))
        scratch = surface.copy()
        original = (180, 60, 15)
        for maximum in (100, 200):
            for ratio in (1., .2, .15, .1, .05, 0., -.1):
                surface.fill(original)
                gray = pygame.transform.grayscale(surface).get_at((0, 0))
                desaturate_hull(surface, scratch, maximum * ratio, maximum)
                result = surface.get_at((0, 0))
                amount = max(0., min(1., 1 - ratio / .2))
                for actual, start, end in zip(result[:3], original, gray[:3]):
                    self.assertAlmostEqual(actual, start + (end - start) * amount, delta=2)
        w = self.app.world
        state = (w.rng.getstate(), w.time, w.player.health)
        w.player.health = 0
        self.app.draw()
        image = pygame.image.tobytes(self.app.canvas.subsurface(VIEWPORT), "RGB")
        self.assertTrue(all(image[i] == image[i + 1] == image[i + 2] for i in range(0, len(image), 3)))
        self.assertNotEqual(self.app.canvas.get_at((1020, 104)).r, self.app.canvas.get_at((1020, 104)).b)
        self.app.draw()
        self.assertEqual(pygame.image.tobytes(self.app.canvas.subsurface(VIEWPORT), "RGB"), image)
        w.player.health = state[2]
        self.assertEqual((w.rng.getstate(), w.time, w.player.health), state)

    def test_temporal_burst_draws_only_during_original_damage_window(self):
        world = self.app.world
        hazards = importlib.import_module(type(world.component("enemy")).__module__ + ".hazards")
        zone = hazards.Zone(Vec(300, 200), 38, .72, 12, source=Vec(200, 200))
        world.player.pos = zone.pos.copy()
        surface = pygame.Surface((960, 480), pygame.SRCALPHA)
        with patch.object(world, "hit_player") as hit:
            zone.update(world, .71)
            zone.draw(None, surface, world)
            self.assertFalse(hit.called)
            self.assertEqual(surface.get_bounding_rect().width, 0)
            zone.update(world, .02)
            hit.assert_called_once_with(12)
            snapshot = (world.rng.getstate(), zone.age, zone.alive, zone.pos.copy())
            zone.draw(None, surface, world)
            self.assertGreater(surface.get_at((300, 200)).a, 0)
            self.assertGreater(surface.get_at((250, 200)).a, 0)
            self.assertGreater(surface.get_at((320, 211)).a, 0)
            self.assertEqual((world.rng.getstate(), zone.age, zone.alive, zone.pos), snapshot)
            zone.update(world, .35)
            self.assertFalse(zone.alive)

    def test_flank_blink_leaves_post_teleport_residue_without_consuming_rng(self):
        w = self.app.world
        w.wave = 4
        enemy = w.enemies[0]
        enemy.pos, enemy.timer, enemy.state = Vec(300, 200), 0., "windup"
        w.player.pos = Vec(700, 250)
        before = enemy.pos.copy()
        w.component("enemy").advance_enemy(w, enemy, .01)
        echo = next(e for e in w.effects if type(e).__name__ == "BlinkEcho")
        self.assertEqual(echo.departure, before)
        self.assertNotEqual(echo.arrival, before)
        rng = w.rng.getstate()
        for reduced in (False, True):
            w.prefs.reduced_motion = reduced
            echo.draw(self.app.graphics, self.app.arena_surface, w)
        self.assertEqual(w.rng.getstate(), rng)
        echo.update(.3)
        self.assertFalse(echo.alive)

    def test_generated_death_sound_decodes_and_respects_effects_mute(self):
        audio = self.app.audio
        self.assertTrue(audio.available)
        self.assertIn("game_over", audio.common_assets)
        self.assertTrue(.3 < audio.sounds["game_over"].get_length() < 1.3)
        self.app.prefs.effects = 0.
        audio.set_volumes()
        audio.stop_effects()
        audio.play("game_over")
        self.assertEqual(len(audio.voices), 1)
        index = next(iter(audio.voices))
        self.assertEqual(pygame.mixer.Channel(index).get_volume(), 0.)
        audio.stop_effects()
        self.assertFalse(audio.voices)
        self.assertFalse(pygame.mixer.Channel(index).get_busy())
