"""Controller polling, menu reachability and input lifecycle without physical hardware."""
import math
from dataclasses import replace
import os
from pathlib import Path
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pygame
from system_panic.app import App
from system_panic.input_devices import Gamepads, MenuRepeat, spatial_focus, stick, A, B, X, START, LB, RB, UP, DOWN, LEFT, RIGHT
from system_panic.model import Controls
from system_panic.preferences import Preferences
from system_panic.paks import Catalog

TEMP = ROOT / "output/test-temp"
TEMP.mkdir(parents=True, exist_ok=True)


class FakePad:
    def __init__(self, identity=41):
        self.id, self.name = identity + 1000, f"Test pad {identity}"
        self._instance_id = identity
        self.axes, self.buttons, self.present = {}, set(), True
        self.closes = 0

    def get_axis(self, axis): return self.axes.get(axis, 0)
    def get_button(self, button): return button in self.buttons
    def attached(self): return self.present
    def as_joystick(self): return self
    def get_instance_id(self): return self._instance_id
    def quit(self): self.closes += 1


class FakeBackend:
    def __init__(self, *pads): self.pads = list(pads)
    def init(self): pass
    def get_count(self): return len(self.pads)
    def is_controller(self, index): return 0 <= index < len(self.pads)
    def Controller(self, index): return self.pads[index]


class GamepadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEMP)
        self.pad = FakePad()
        self.backend = FakeBackend(self.pad)
        self.devices = Gamepads(self.backend)
        self.app = App(Path(self.temp.name), 24, gamepads=self.devices)
        self.app.draw()
        self.tick()  # Neutral first frame arms a newly opened controller.

    def tearDown(self):
        self.devices.close()
        pygame.quit()
        self.temp.cleanup()

    def tick(self, elapsed=1 / 60):
        self.app.update(elapsed)
        self.app.draw()

    def press(self, button):
        self.pad.buttons.add(button)
        self.tick()
        self.pad.buttons.clear()
        self.tick()

    def focus(self, id):
        self.app.draw()
        self.app.focus = next(i for i, b in enumerate(self.app.buttons) if b.id == id)
        self.app.keyboard_focus = True

    def test_stick_and_dpad_produce_identical_digital_controls_and_menu_steps(self):
        self.assertEqual(stick(.1, -.1, .18), (0., 0.))
        self.assertEqual(stick(.19, 0, .18), (1., 0.))
        self.assertEqual(stick(.59, 0, .18), stick(1, 0, .18))
        self.assertAlmostEqual(math.hypot(*stick(1, 1, .18)), 1)
        directions = ((1,0,{RIGHT}),(-1,0,{LEFT}),(0,1,{DOWN}),(0,-1,{UP}),
                      (1,1,{DOWN,RIGHT}),(-1,-1,{UP,LEFT}),(1,-1,{UP,RIGHT}),(-1,1,{DOWN,LEFT}))
        for x,y,buttons in directions:
            self.pad.axes.clear()
            self.pad.buttons = buttons
            digital = self.devices.poll()
            self.pad.buttons.clear()
            for magnitude in (.2,.6,1):
                self.pad.axes = {0:int(x*32767*magnitude),1:int(y*32767*magnitude)}
                analog = self.devices.poll()
                self.assertEqual(analog.controls,digital.controls)
                self.assertEqual(analog.menu,digital.menu)
                stick_repeat,pad_repeat=MenuRepeat(),MenuRepeat()
                for _ in range(100):
                    self.assertEqual(stick_repeat.update(*analog.menu,1/60),pad_repeat.update(*digital.menu,1/60))

    def test_trigger_face_and_shoulder_map_to_neutral_pak_controls(self):
        self.pad.axes[5] = 20000
        self.assertTrue(self.devices.poll().controls.fire)
        self.pad.axes.clear()
        self.pad.buttons = {A, X}
        frame = self.devices.poll()
        self.assertEqual(frame.controls, Controls(fire=True, special=True))
        self.pad.buttons = {LB}
        self.assertTrue(self.devices.poll().controls.special)
        self.assertFalse(self.devices.poll().pressed)

    def test_noise_does_not_move_focus_or_steal_mouse_hints(self):
        self.app.input_device, self.app.keyboard_focus = "mouse", False
        before = self.app.focus
        self.pad.axes[0] = 2000
        for _ in range(60): self.tick()
        self.assertEqual((self.app.input_device, self.app.focus), ("mouse", before))

    def test_menu_confirm_does_not_leak_fire_and_pause_requires_release(self):
        self.focus("solo:signal_runner")
        self.pad.buttons = {A}
        self.tick()
        self.assertEqual(self.app.route, "game")
        self.app.world.phase = "active"
        self.app.world.cover = []
        for _ in range(30): self.tick()
        self.assertFalse(self.app.world.projectiles)
        self.pad.buttons.clear()
        self.tick()
        self.pad.buttons = {A}
        self.tick()
        self.assertTrue(self.app.world.projectiles)
        self.pad.buttons.clear()
        self.tick()
        self.pad.buttons = {START}
        self.tick()
        self.assertEqual(self.app.route, "pause")
        before = self.app.world.time
        for _ in range(60): self.tick()
        self.assertEqual((self.app.route, self.app.world.time), ("pause", before))
        self.pad.buttons.clear()
        self.tick()
        self.press(START)
        self.assertEqual(self.app.route, "game")

    def test_menu_navigation_toggles_paks_and_nested_back_returns_to_pause(self):
        self.focus("toggle:void_drifter")
        self.press(A)
        self.assertNotIn("void_drifter", self.app.prefs.enabled)
        self.focus("start")
        self.press(A)
        self.press(START)
        self.focus("pause-settings")
        self.press(A)
        self.focus("controls")
        self.press(A)
        self.assertEqual(self.app.route, "controls")
        old = self.app.prefs.gamepad_deadzone
        self.focus("gamepad_deadzone")
        self.press(A)
        self.assertGreater(self.app.prefs.gamepad_deadzone, old)
        self.assertEqual(self.app.store.load().gamepad_deadzone, self.app.prefs.gamepad_deadzone)
        self.press(B)
        self.assertEqual(self.app.route, "settings")
        self.press(B)
        self.assertEqual(self.app.route, "pause")
        self.press(B)
        self.assertEqual(self.app.route, "game")

    def test_directions_reach_every_visible_button_on_every_screen(self):
        self.app.start()
        for route in ("home", "settings", "controls", "help", "credits", "paks", "pause", "outcome"):
            with self.subTest(route=route):
                self.app.navigate(route)
                self.app.draw()
                rects = [b.rect for b in self.app.buttons]
                seen, pending = {self.app.preferred_focus()}, [self.app.preferred_focus()]
                while pending:
                    current = pending.pop()
                    for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        target = spatial_focus(rects, current, direction)
                        if target not in seen:
                            seen.add(target)
                            pending.append(target)
                self.assertEqual(len(seen), len(rects), [b.id for i, b in enumerate(self.app.buttons) if i not in seen])
                self.assertTrue(all(self.app.canvas.get_rect().contains(r) for r in rects))

    def test_direction_repeat_has_hysteresis_and_no_burst_after_long_frames(self):
        repeat = MenuRepeat()
        self.assertIsNone(repeat.update(.5, 0, .1))
        self.assertEqual(repeat.update(.7, 0, .01), (1, 0))
        self.assertIsNone(repeat.update(.4, 0, .1))
        self.assertEqual(repeat.update(.7, 0, 2), (1, 0))
        self.assertIsNone(repeat.update(.7, 0, .01))
        repeat.block()
        self.assertIsNone(repeat.update(.8, 0, 1))
        self.assertIsNone(repeat.update(0, 0, .01))
        self.assertEqual(repeat.update(-.8, 0, .01), (-1, 0))

    def test_active_disconnect_pauses_and_clears_input_without_auto_resume(self):
        self.app.start("signal_runner")
        self.tick()
        self.pad.axes[0] = 32767
        self.pad.present = False
        before = self.app.world.time
        self.tick()
        self.assertEqual((self.app.route, self.app.world.time), ("pause", before))
        self.assertFalse(self.devices.connected)
        replacement = FakePad(99)
        replacement.buttons.add(A)
        self.backend.pads.append(replacement)
        self.app.handle_event(pygame.event.Event(pygame.CONTROLLERDEVICEADDED, device_index=1))
        for _ in range(20): self.tick()
        self.assertEqual(self.app.route, "pause")
        replacement.buttons.clear()
        self.tick()
        replacement.buttons.add(START)
        self.tick()
        self.assertEqual(self.app.route, "game")

    def test_instance_ids_hotplug_selection_and_duplicate_joystick_events(self):
        second = FakePad(99)
        self.backend.pads.append(second)
        self.app.handle_event(pygame.event.Event(pygame.CONTROLLERDEVICEADDED, device_index=1))
        self.assertEqual(set(self.devices.devices), {41, 99})
        self.app.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, instance_id=99, button=A))
        self.assertEqual(self.devices.active_id, 41)
        self.app.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, instance_id=99, button=A))
        self.assertEqual(self.devices.active_id, 99)
        self.app.handle_event(pygame.event.Event(pygame.CONTROLLERDEVICEREMOVED, instance_id=41))
        self.assertEqual(self.devices.active_id, 99)
        self.assertEqual(second.closes, 0)

    def test_focus_loss_ignores_pad_actions_until_focus_and_neutral_return(self):
        self.app.start()
        self.app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.pad.buttons = {A}
        for _ in range(30): self.tick()
        self.assertEqual(self.app.route, "pause")
        self.app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
        self.tick()
        self.assertEqual(self.app.route, "pause")
        self.pad.buttons.clear()
        self.tick()
        self.press(A)
        self.assertEqual(self.app.route, "game")

    def test_keyboard_remains_available_when_controller_fails_or_disconnects(self):
        self.pad.present = False
        self.tick()
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
        self.assertEqual(self.app.route, "game")
        self.assertEqual(self.app.input_device, "keyboard")

    def test_backend_errors_and_unmapped_devices_leave_keyboard_usable(self):
        class Unavailable(FakeBackend):
            def init(self): raise pygame.error("no controller subsystem")
        devices = Gamepads(Unavailable())
        self.assertFalse(devices.connected)
        self.assertIn("no controller", devices.error)
        self.assertEqual(devices.poll().controls, Controls())
        class Unmapped(FakeBackend):
            def is_controller(self, index): return False
        self.assertFalse(Gamepads(Unmapped(FakePad())).connected)

    def test_shoulders_change_library_pages_and_return_focus_to_valid_buttons(self):
        catalog = self.app.catalog
        extra = replace(catalog.paks[0], id="extra", name="Extra Pak")
        self.app.catalog = Catalog((*catalog.paks, extra), catalog.issues, catalog.roots)
        self.app.graphics.catalog = self.app.catalog
        self.app.draw()
        last_page=len(catalog.paks)//6
        for _ in range(last_page): self.press(RB)
        self.assertEqual(self.app.library_page, last_page)
        self.assertIn("solo:extra", [b.id for b in self.app.buttons])
        self.assertLess(self.app.focus, len(self.app.buttons))
        self.press(LB)
        self.assertEqual(self.app.library_page, last_page-1)

    def test_incomplete_library_defaults_to_status_instead_of_quit(self):
        catalog = self.app.catalog
        self.app.catalog = Catalog((), (), catalog.roots)
        self.app.graphics.catalog = self.app.catalog
        self.app.navigate("home")
        self.tick()
        self.assertEqual(self.app.buttons[self.app.focus].id, "pak-status")
        self.press(A)
        self.assertEqual(self.app.route, "paks")
        self.assertTrue(self.app.running)

    def test_periodic_shuffle_resumes_held_gamepad_input_without_rearming(self):
        self.app.start("signal_runner")
        self.tick()
        self.pad.buttons = {A}
        self.app.world.phase = "active"
        self.app.world.cover = []
        self.tick()
        self.assertTrue(self.devices.gameplay(self.devices.poll()).fire)
        self.app.world.shuffle()
        for _ in range(20): self.tick()
        self.assertTrue(self.devices.gameplay(self.devices.poll()).fire)

    def test_deadzone_preferences_validate_old_profiles_and_nonfinite_values(self):
        self.assertEqual(Preferences.from_dict({}).gamepad_deadzone, .18)
        for value, expected in ((-1, .05), (5, .45), (float("nan"), .18), (float("inf"), .18), (True, .18), (".2", .18)):
            self.assertEqual(Preferences.from_dict({"gamepad_deadzone": value}).gamepad_deadzone, expected)
