import os
from pathlib import Path
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pygame
from system_panic.app import App
from system_panic.model import Controls
from system_panic.paks import PAKS

TEMP_ROOT = Path(__file__).resolve().parents[1] / "output" / "test-temp"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


class UITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.app = App(Path(self.temp.name), seed=24)
        self.app.draw()

    def tearDown(self):
        pygame.quit()
        self.temp.cleanup()

    def click(self, id):
        self.app.draw()
        button = next(b for b in self.app.buttons if b.id == id)
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=button.rect.center))

    def key(self, key):
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0))

    def test_enter_starts_pause_and_focus_loss_freeze_the_world(self):
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.route, "game")
        for _ in range(120):
            self.app.update(1 / 60, Controls(fire=True))
        before = self.app.world.time
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.route, "pause")
        self.app.update(2, Controls(fire=True))
        self.assertEqual(self.app.world.time, before)
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.route, "game")
        self.app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertEqual(self.app.route, "pause")

    def test_pak_selection_saved_and_empty_selection_prevented(self):
        for pak in PAKS[:-1]:
            self.click("toggle:" + pak.id)
        self.click("toggle:" + PAKS[-1].id)
        self.assertEqual(self.app.prefs.enabled, [PAKS[-1].id])
        self.assertEqual(self.app.store.load().enabled, [PAKS[-1].id])
        self.click("start")
        self.assertEqual(set(self.app.world.mix.values()), {PAKS[-1].id})

    def test_solo_button_settings_and_retry(self):
        self.click("settings")
        self.click("mix_mode")
        self.click("music-")
        self.click("motion")
        self.click("back")
        self.assertEqual(self.app.prefs.mix_mode, "coherent")
        self.assertTrue(self.app.prefs.reduced_motion)
        self.assertAlmostEqual(self.app.prefs.music, .45)
        self.click("solo:sky_forge")
        self.assertEqual(self.app.world.solo, "sky_forge")
        self.app.world.score = 4321
        self.app.world.phase = "dead"
        self.app.update(.016)
        self.assertEqual(self.app.route, "outcome")
        self.assertEqual(self.app.store.load().high_score, 4321)
        self.click("retry")
        self.assertEqual(self.app.route, "game")
        self.assertEqual(self.app.world.score, 0)
        self.assertEqual(self.app.world.player.health, 100)
        self.assertEqual(self.app.world.solo, "sky_forge")

    def test_all_screens_render_with_buttons_inside_canvas(self):
        self.app.prefs.shuffle_seconds = 6  # Valid hand-edited value outside preset buttons.
        for route in ("home", "settings", "help", "credits", "game", "pause", "outcome"):
            if route in ("game", "pause", "outcome") and not self.app.world:
                self.app.start()
            self.app.route = route
            self.app.draw()
            for button in self.app.buttons:
                self.assertTrue(self.app.canvas.get_rect().contains(button.rect), button.id)
