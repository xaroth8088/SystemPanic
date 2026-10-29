"""Player-facing static Remix creation, favorites, pause capture and controller menus."""
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
from system_panic.app import App, SIZE
from system_panic.input_devices import A, B, DOWN, LEFT, RIGHT, UP, Gamepads, spatial_focus
from system_panic.model import Controls
from system_panic.paks import Catalog, CHANNELS, get_catalog

TEMP_ROOT = ROOT / "output/test-temp"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


class FakePad:
    id, name = 17, "Remix test pad"

    def __init__(self):
        self.buttons = set()

    def get_axis(self, axis): return 0
    def get_button(self, button): return button in self.buttons
    def attached(self): return True
    def as_joystick(self): return self
    def get_instance_id(self): return 17
    def quit(self): pass


class FakeBackend:
    def __init__(self, pad): self.pad = pad
    def init(self): pass
    def get_count(self): return 1
    def is_controller(self, index): return index == 0
    def Controller(self, index): return self.pad


class RemixUITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.directory = Path(self.temp.name)
        self.catalog = get_catalog()
        self.pad = FakePad()
        self.devices = Gamepads(FakeBackend(self.pad))
        self.app = App(self.directory, seed=24, catalog=self.catalog, gamepads=self.devices)
        self.tick()

    def tearDown(self):
        if self.app.world:
            self.app.world.close()
        self.devices.close()
        pygame.quit()
        self.temp.cleanup()

    def tick(self):
        self.app.update(1 / 60, Controls())
        self.app.draw()

    def click(self, id):
        self.app.draw()
        button = next(b for b in self.app.buttons if b.id == id)
        rect = self.app.presentation_rect()
        pos = (rect.x + button.rect.centerx * rect.width / SIZE[0],
               rect.y + button.rect.centery * rect.height / SIZE[1])
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))

    def key(self, key):
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0))

    def type_name(self, name):
        self.click("name-clear")
        self.app.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=name))

    def save_favorite(self, name="Favorite mix"):
        self.click("remix-save")
        self.type_name(name)
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.route, "remix")
        return self.app.remixes[-1]

    def choose_provider(self, channel, provider):
        self.click("remix-channel:" + channel)
        self.assertEqual(self.app.route, "remix-picker")
        for _ in range(len(self.catalog.paks)):
            self.app.draw()
            if any(b.id == "provider:" + provider for b in self.app.buttons):
                break
            self.click("remix_picker_page:next")
        self.click("provider:" + provider)
        self.assertEqual(self.app.route, "remix")

    def test_choose_six_channels_save_rename_delete_and_reload(self):
        self.click("remix")
        expected = {channel: self.catalog.paks[index + 6].id
                    for index, channel in enumerate(CHANNELS)}
        for channel, provider in expected.items():
            self.choose_provider(channel, provider)
        self.assertEqual(self.app.remix_mix, expected)
        favorite = self.save_favorite()
        self.assertEqual(self.app.remix_store.load()[0].mix, expected)
        self.assertEqual(self.app.remix_selected, favorite.id)
        self.click("remix-rename")
        self.type_name("Reworked favorite")
        self.click("name-save")
        self.assertEqual(len(self.app.remixes), 1)
        renamed = self.app.remix_store.load()[0]
        self.assertEqual((renamed.id, renamed.name, renamed.mix),
                         (favorite.id, "Reworked favorite", expected))
        self.click("back")
        self.click("remix")
        self.click("remix-saved")
        self.click("favorite:" + favorite.id)
        self.assertEqual(self.app.remix_mix, expected)
        self.click("remix-delete")
        self.click("delete-cancel")
        self.assertEqual(len(self.app.remixes), 1)
        self.click("remix-delete")
        self.click("delete-confirm")
        self.assertEqual(self.app.remixes, [])
        self.assertEqual(self.app.remix_store.load(), [])

    def test_static_launch_and_retry_preserve_choices_independent_of_main_pool(self):
        self.app.open_remix()
        mix = {channel: self.catalog.paks[index].id for index, channel in enumerate(CHANNELS)}
        self.app.remix_mix = mix.copy()
        self.app.prefs.enabled = [self.catalog.paks[-1].id]
        before_preferences = vars(self.app.prefs).copy()
        self.click("remix-play")
        self.assertEqual(self.app.route, "game")
        self.assertEqual(self.app.world.mix, mix)
        self.assertFalse(self.app.world.can_shuffle)
        self.assertEqual(vars(self.app.prefs), before_preferences)
        self.app.remix_mix["music"] = self.catalog.paks[-1].id
        self.assertEqual(self.app.world.mix, mix)
        self.app.world.score = 777
        self.app.world.phase = "dead"
        self.app.update(1 / 60, Controls())
        self.assertEqual(self.app.route, "game-over")
        self.app.update(1.4, Controls())
        self.click("retry")
        self.assertEqual(self.app.world.mix, mix)
        self.assertEqual((self.app.world.wave, self.app.world.score), (1, 0))
        self.assertFalse(self.app.world.can_shuffle)

    def test_pause_capture_saves_current_mix_and_preserves_paused_run(self):
        self.app.start()
        self.app.world.shuffle()
        self.key(pygame.K_ESCAPE)
        world = self.app.world
        current = world.mix.copy()
        before = (world.time, world.wave, world.score, world.rng.getstate())
        self.click("save-mix")
        self.app.update(3, Controls(fire=True))
        self.click("name-cancel")
        self.assertEqual(self.app.route, "pause")
        self.assertEqual(self.app.remixes, [])
        self.click("save-mix")
        self.type_name("Captured shuffle")
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.route, "pause")
        self.assertIs(self.app.world, world)
        self.assertEqual((world.time, world.wave, world.score, world.rng.getstate()), before)
        saved = self.app.remix_store.load()[0]
        self.assertEqual(saved.mix, current)
        self.click("resume")
        self.assertEqual(self.app.route, "game")
        self.app.home()
        self.app.open_remix()
        self.click("remix-saved")
        self.click("favorite:" + saved.id)
        self.click("remix-play")
        self.assertEqual(self.app.world.mix, current)
        self.assertEqual(self.app.world.wave, 1)
        self.assertFalse(self.app.world.can_shuffle)

    def test_failed_save_keeps_name_editor_and_old_favorite_until_retry(self):
        self.app.open_remix()
        favorite = self.save_favorite("Keep me")
        original = self.app.remix_store.path.read_bytes()
        self.click("remix-rename")
        self.type_name("New name")
        with patch("system_panic.remixes.RemixStore.save", return_value=False):
            self.click("name-save")
        self.assertEqual(self.app.route, "remix-name")
        self.assertEqual(self.app.remixes[0].name, "Keep me")
        self.assertEqual(self.app.remix_store.path.read_bytes(), original)
        self.click("name-save")
        self.assertEqual(self.app.remix_store.load()[0].name, "New name")
        self.assertEqual(self.app.remixes[0].id, favorite.id)

    def test_failed_create_and_delete_leave_favorites_unchanged(self):
        self.app.open_remix()
        self.click("remix-save")
        self.type_name("Retry creation")
        with patch("system_panic.remixes.RemixStore.save", return_value=False):
            self.click("name-save")
        self.assertEqual(self.app.route, "remix-name")
        self.assertEqual(self.app.remixes, [])
        self.assertFalse(self.app.remix_store.path.exists())
        self.click("name-save")
        favorite = self.app.remixes[0]
        original = self.app.remix_store.path.read_bytes()
        self.click("remix-delete")
        with patch("system_panic.remixes.RemixStore.save", return_value=False):
            self.click("delete-confirm")
        self.assertEqual(self.app.route, "remix-delete")
        self.assertEqual(self.app.remix_selected, favorite.id)
        self.assertEqual(self.app.remix_store.path.read_bytes(), original)
        self.assertEqual(len(self.app.remixes), 1)
        self.click("delete-confirm")
        self.assertEqual(self.app.route, "remix")
        self.assertEqual(self.app.remix_store.load(), [])

    def test_save_as_new_preserves_original_and_saved_pages_survive_reload(self):
        self.app.open_remix()
        original = self.save_favorite("Original")
        first_mix = original.mix.copy()
        self.choose_provider("pilot", self.catalog.paks[-1].id)
        self.assertIsNone(self.app.remix_selected)
        copy = self.save_favorite("Copy")
        self.assertNotEqual(original.id, copy.id)
        self.assertEqual(self.app.remixes[0].mix, first_mix)
        self.assertNotEqual(original.mix, copy.mix)
        for index in range(3):
            self.save_favorite(f"Favorite {index}")
        last = self.app.remixes[-1]
        self.app.remixes = self.app.remix_store.load()
        self.click("remix-saved")
        self.app.draw()
        self.assertNotIn("favorite:" + last.id, [b.id for b in self.app.buttons])
        self.click("remix_saved_page:next")
        self.assert_reachable()
        self.click("favorite:" + last.id)
        self.assertEqual(self.app.remix_selected, last.id)
        self.assertEqual(self.app.remix_mix, last.mix)
        self.click("remix-delete")
        self.click("delete-confirm")
        self.click("remix-saved")
        self.app.draw()
        self.assertEqual(self.app.remix_saved_page, 0)
        self.assertNotIn("remix_saved_page:next", [b.id for b in self.app.buttons])

    def test_missing_provider_favorite_is_retained_and_can_be_renamed_or_repaired(self):
        self.app.open_remix()
        missing_id = self.catalog.paks[0].id
        self.app.remix_mix = {channel: missing_id for channel in CHANNELS}
        favorite = self.save_favorite("Temporarily unavailable")
        reduced = Catalog(tuple(p for p in self.catalog.paks if p.id != missing_id), (), self.catalog.roots)
        self.app.catalog = reduced
        self.app.remix_store.catalog = reduced
        self.app.remixes = self.app.remix_store.load()
        self.click("remix-saved")
        self.click("favorite:" + favorite.id)
        self.app.draw()
        self.assertNotIn("remix-play", [b.id for b in self.app.buttons])
        self.app.play_remix()
        self.assertIsNone(self.app.world)
        self.assertEqual(self.app.route, "remix")
        self.click("remix-rename")
        self.type_name("Still mine")
        self.click("name-save")
        self.assertEqual(self.app.remix_store.load()[0].name, "Still mine")
        self.assertEqual(self.app.remix_mix, {channel: missing_id for channel in CHANNELS})
        for channel in CHANNELS:
            self.choose_provider(channel, reduced.paks[0].id)
        self.click("remix-play")
        self.assertEqual(self.app.route, "game")

    def test_keyboard_name_editing_and_cancel_do_not_save(self):
        self.app.open_remix()
        self.click("remix-save")
        self.type_name("A mix")
        self.key(pygame.K_BACKSPACE)
        self.assertEqual(self.app.remix_name, "A mi")
        self.app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.app.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="ignored"))
        self.assertEqual(self.app.remix_name, "A mi")
        self.app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.route, "remix")
        self.assertEqual(self.app.remixes, [])
        self.app.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="ignored"))
        self.assertEqual(self.app.remixes, [])

    def assert_reachable(self):
        self.app.draw()
        rects = [b.rect for b in self.app.buttons]
        seen = {self.app.preferred_focus()}
        pending = list(seen)
        while pending:
            current = pending.pop()
            for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                target = spatial_focus(rects, current, direction)
                if target not in seen:
                    seen.add(target)
                    pending.append(target)
        self.assertEqual(len(seen), len(rects), [b.id for i, b in enumerate(self.app.buttons) if i not in seen])
        for rect in rects:
            self.assertTrue(self.app.canvas.get_rect().contains(rect))

    def test_new_routes_have_reachable_controller_controls(self):
        self.app.open_remix()
        self.save_favorite()
        self.assert_reachable()
        self.click("remix-channel:pilot")
        self.assert_reachable()
        self.key(pygame.K_ESCAPE)
        self.click("remix-saved")
        self.assert_reachable()
        self.key(pygame.K_ESCAPE)
        self.click("remix-save")
        self.assert_reachable()
        self.key(pygame.K_ESCAPE)
        self.click("remix-delete")
        self.assert_reachable()

    def press(self, button):
        self.pad.buttons = {button}
        self.tick()
        self.pad.buttons.clear()
        self.tick()

    def pad_choose(self, id):
        self.app.draw()
        rects = [b.rect for b in self.app.buttons]
        target = next(i for i, b in enumerate(self.app.buttons) if b.id == id)
        start = self.app.focus if self.app.keyboard_focus else self.app.preferred_focus()
        pending = [(start, [])]
        seen = {start}
        route = None
        while pending:
            current, path = pending.pop(0)
            if current == target:
                route = path
                break
            for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                following = spatial_focus(rects, current, direction)
                if following not in seen:
                    seen.add(following)
                    pending.append((following, path + [direction]))
        self.assertIsNotNone(route, id)
        directions = {(1, 0): RIGHT, (-1, 0): LEFT, (0, 1): DOWN, (0, -1): UP}
        for direction in route:
            self.press(directions[direction])
        self.assertEqual(self.app.buttons[self.app.focus].id, id)
        self.press(A)

    def test_gamepad_can_name_save_and_return_to_paused_run(self):
        self.app.start()
        self.app.navigate("pause")
        self.tick()
        self.pad_choose("save-mix")
        self.assertEqual(self.app.route, "remix-name")
        self.pad_choose("name-clear")
        for char in "PAD MIX":
            self.pad_choose("name-key:" + char)
        self.assertEqual(self.app.remix_name, "PAD MIX")
        self.pad_choose("name-save")
        self.assertEqual(self.app.route, "pause")
        self.assertEqual(self.app.remix_store.load()[0].name, "PAD MIX")
        self.press(B)
        self.assertEqual(self.app.route, "game")


if __name__ == "__main__":
    unittest.main()
