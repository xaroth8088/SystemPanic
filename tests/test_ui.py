import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pygame
from system_panic.app import App, SIZE
from system_panic.model import Controls
from system_panic.paks import get_catalog
PAKS = get_catalog().paks

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
        for _ in range((len(self.app.catalog.paks)+5)//6):
            if any(b.id==id for b in self.app.buttons): break
            next_page=next((b for b in self.app.buttons if b.id=="library_page:next"),None)
            if next_page is None: break
            self.app.activate(next_page)
            self.app.draw()
        button = next(b for b in self.app.buttons if b.id == id)
        target=self.app.presentation_rect()
        point=(target.x+button.rect.centerx*target.width/SIZE[0],target.y+button.rect.centery*target.height/SIZE[1])
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))

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
        self.click("difficulty")
        self.click("music-")
        self.click("motion")
        self.click("back")
        self.assertEqual(self.app.prefs.difficulty, "intense")
        self.assertTrue(self.app.prefs.reduced_motion)
        self.assertAlmostEqual(self.app.prefs.music, .50)
        self.click("solo:sky_forge")
        self.assertEqual(self.app.world.solo, "sky_forge")
        self.app.world.score = 4321
        self.app.world.phase = "dead"
        self.app.update(.016)
        self.assertEqual(self.app.route, "game-over")
        self.app.update(1.4)
        self.assertEqual(self.app.route, "outcome")
        self.assertEqual(self.app.store.load().high_score, 4321)
        self.click("retry")
        self.assertEqual(self.app.route, "game")
        self.assertEqual(self.app.world.score, 0)
        self.assertEqual(self.app.world.player.health, 100)
        self.assertEqual(self.app.world.solo, "sky_forge")

    def test_all_screens_render_with_buttons_inside_canvas(self):
        self.app.prefs.shuffle_seconds = 6  # Valid hand-edited value outside preset buttons.
        for route in ("home", "settings", "display", "controls", "help", "credits", "paks", "game", "pause", "outcome"):
            if route in ("game", "pause", "outcome") and not self.app.world:
                self.app.start()
            self.app.route = route
            self.app.draw()
            for button in self.app.buttons:
                self.assertTrue(self.app.canvas.get_rect().contains(button.rect), button.id)

    def test_render_resolution_preserves_world_surfaces_and_scaled_pointer_navigation(self):
        self.app.start("signal_runner")
        self.app.navigate("pause")
        self.app.draw()
        self.click("pause-settings")
        self.click("display")
        world=self.app.world
        canvas,arena=self.app.canvas,self.app.arena_surface
        before=(world.time,world.player.pos.copy(),world.rng.getstate(),world.wave)
        for resolution in ("1280x720","1024x768","960x600","1920x1080"):
            self.click("resolution:"+resolution)
            self.assertEqual(self.app.window.get_size(),tuple(map(int,resolution.split("x"))))
            self.assertEqual(self.app.store.load().render_resolution,resolution)
            self.assertIs(self.app.world,world)
            self.assertIs(self.app.canvas,canvas)
            self.assertIs(self.app.arena_surface,arena)
            self.assertEqual(canvas.get_size(),(1280,800))
            self.assertEqual(arena.get_size(),(960,480))
            self.assertEqual((world.time,world.player.pos,world.rng.getstate(),world.wave),before)
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.route,"settings")
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.route,"pause")
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.route,"game")

    def test_saved_resolution_applies_at_startup_and_fullscreen_uses_selected_output(self):
        self.app.set_render_resolution("1280x720")
        self.app.quit()
        self.app=App(Path(self.temp.name),seed=24)
        self.assertEqual(self.app.window.get_size(),(1280,720))
        original=pygame.display.set_mode
        with patch("system_panic.app.pygame.display.set_mode",wraps=original) as mode:
            self.app.cycle("fullscreen",[False,True])
            mode.assert_called_once_with((1280,720),pygame.FULLSCREEN)
        self.app.cycle("fullscreen",[False,True])
        self.assertEqual(self.app.window.get_size(),(1280,720))

    def test_unavailable_display_mode_recovers_to_automatic_window(self):
        original=pygame.display.set_mode
        calls=[]
        def unavailable(size,flags):
            calls.append((size,flags))
            if size==(1920,1080):raise pygame.error("unsupported mode")
            return original(size,flags)
        with patch("system_panic.app.pygame.display.set_mode",side_effect=unavailable):
            self.app.set_render_resolution("1920x1080")
        self.assertEqual(self.app.prefs.render_resolution,"auto")
        self.assertFalse(self.app.prefs.fullscreen)
        self.assertEqual(self.app.window.get_size(),SIZE)
        self.assertEqual(self.app.store.load().render_resolution,"auto")
        self.assertIn("unavailable",self.app.toast)

    def test_both_volume_controls_use_five_percentage_points_and_clamp_at_endpoints(self):
        self.click("settings")
        self.click("music-")
        self.click("effects+")
        self.assertEqual(self.app.prefs.music,.5)
        self.assertEqual(self.app.prefs.effects,.7)
        self.click("music+")
        self.click("effects-")
        self.assertEqual((self.app.prefs.music,self.app.prefs.effects),(.55,.65))
        self.app.prefs.music=0.
        self.app.prefs.effects=1.
        self.click("music-")
        self.click("effects+")
        self.assertEqual((self.app.prefs.music,self.app.prefs.effects),(0.,1.))
        self.assertEqual((self.app.store.load().music,self.app.store.load().effects),(0.,1.))

    def test_level_eight_continues_play_and_preferences_have_no_finish_toggle(self):
        self.app.route = "settings"
        self.app.draw()
        self.assertNotIn("endless", [button.id for button in self.app.buttons])
        self.app.start("signal_runner")
        world = self.app.world
        world.wave = 8
        world.enemies.clear()
        world.phase = "clear"
        world.phase_timer = 0
        self.app.update(1 / 60, Controls())
        self.assertEqual(self.app.route, "game")
        self.assertEqual(world.phase, "active")
        self.assertEqual(world.wave, 9)
        self.assertEqual(len(world.enemies), 9)
        self.assertFalse(self.app.recorded)
