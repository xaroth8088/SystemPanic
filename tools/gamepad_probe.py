"""Native SDL virtual-pad exercise, also loaded as external code by the frozen QA run."""
import ctypes
import os
from pathlib import Path

# Only the QA process accepts background joystick updates under SDL's dummy window.
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

import pygame
from system_panic.input_devices import spatial_focus, A, B, X, START, LB, RB, UP, DOWN, LEFT, RIGHT


class VirtualPad:
    """A real SDL input device: events and polled state go through the shipping backend."""
    def __init__(self):
        library = Path(pygame.__file__).with_name("SDL2.dll")
        if not library.is_file():
            raise RuntimeError("Native gamepad QA currently requires the Windows Pygame SDL2.dll")
        self.sdl = ctypes.CDLL(str(library))
        signatures = {
            "SDL_JoystickAttachVirtual": ([ctypes.c_int] * 4, ctypes.c_int),
            "SDL_JoystickOpen": ([ctypes.c_int], ctypes.c_void_p),
            "SDL_JoystickSetVirtualAxis": ([ctypes.c_void_p, ctypes.c_int, ctypes.c_int16], ctypes.c_int),
            "SDL_JoystickSetVirtualButton": ([ctypes.c_void_p, ctypes.c_int, ctypes.c_uint8], ctypes.c_int),
            "SDL_JoystickInstanceID": ([ctypes.c_void_p], ctypes.c_int32),
            "SDL_JoystickGetDeviceInstanceID": ([ctypes.c_int], ctypes.c_int32),
            "SDL_JoystickDetachVirtual": ([ctypes.c_int], ctypes.c_int),
            "SDL_JoystickClose": ([ctypes.c_void_p], None),
            "SDL_JoystickUpdate": ([], None),
            "SDL_NumJoysticks": ([], ctypes.c_int),
            "SDL_SetHint": ([ctypes.c_char_p, ctypes.c_char_p], ctypes.c_int),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.sdl, name)
            function.argtypes, function.restype = arguments, result
        self.sdl.SDL_SetHint(b"SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", b"1")
        index = self.sdl.SDL_JoystickAttachVirtual(1, 6, 15, 0)
        assert index >= 0
        self.joystick = self.sdl.SDL_JoystickOpen(index)
        assert self.joystick
        self.identity = self.sdl.SDL_JoystickInstanceID(self.joystick)
        self.neutral()

    def axis(self, index, value):
        assert self.sdl.SDL_JoystickSetVirtualAxis(self.joystick, index, value) == 0

    def button(self, index, down):
        assert self.sdl.SDL_JoystickSetVirtualButton(self.joystick, index, int(down)) == 0

    def neutral(self):
        for axis in range(6): self.axis(axis, -32768 if axis >= 4 else 0)
        for button in range(15): self.button(button, False)

    def detach(self):
        if self.joystick is None:
            return
        for index in range(self.sdl.SDL_NumJoysticks()):
            if self.sdl.SDL_JoystickGetDeviceInstanceID(index) == self.identity:
                assert self.sdl.SDL_JoystickDetachVirtual(index) == 0
                break
        self.sdl.SDL_JoystickClose(self.joystick)
        self.joystick = None


def exercise(app, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    physical_count = len(app.gamepads.devices)
    pad, replacement = VirtualPad(), None
    steps = 0
    fired = []
    original_play = app.audio.play_asset

    def observe_sound(asset, **options):
        if asset.path.name == "shot.ogg": fired.append(asset.path)
        return original_play(asset, **options)

    app.audio.play_asset = observe_sound

    def tick(count=1):
        nonlocal steps
        for _ in range(count):
            pad.sdl.SDL_JoystickUpdate()
            for event in pygame.event.get(): app.handle_event(event)
            app.update(1 / 60)
            steps += 1
        app.draw()

    def press(button):
        pad.button(button, True)
        tick()
        pad.button(button, False)
        tick()

    def walk(target_id):
        """Use directional buttons only, never assign UI focus or call button actions."""
        app.draw()
        for _ in range((len(app.catalog.paks)+5)//6):
            if any(b.id==target_id for b in app.buttons): break
            if not any(b.id=="library_page:next" for b in app.buttons): break
            press(RB)
        target = next(i for i, b in enumerate(app.buttons) if b.id == target_id)
        start = app.focus if app.keyboard_focus else app.preferred_focus()
        pending, paths = [start], {start: []}
        rects = [b.rect for b in app.buttons]
        while pending and target not in paths:
            current = pending.pop(0)
            for direction, button in (((1, 0), RIGHT), ((-1, 0), LEFT), ((0, 1), DOWN), ((0, -1), UP)):
                next_index = spatial_focus(rects, current, direction)
                if next_index not in paths:
                    paths[next_index] = paths[current] + [button]
                    pending.append(next_index)
        assert target in paths, target_id
        for button in paths[target]: press(button)
        assert app.buttons[app.focus].id == target_id, (target_id, app.buttons[app.focus].id)

    def snapshot(name):
        app.draw()
        pygame.image.save(app.canvas, output / (name + ".png"))

    runs = []
    try:
        tick(2)
        assert pad.identity in app.gamepads.devices
        app.gamepads.select(pad.identity)
        tick(2)
        walk("settings")
        press(A)
        assert app.route == "settings"
        snapshot("settings")
        walk("controls")
        press(A)
        assert app.route == "controls"
        walk("gamepad_deadzone")
        before = app.prefs.gamepad_deadzone
        press(A)
        assert app.prefs.gamepad_deadzone > before
        assert app.store.load().gamepad_deadzone == app.prefs.gamepad_deadzone
        snapshot("controls")
        press(B)
        assert app.route == "settings"
        press(B)
        assert app.route == "home"
        snapshot("library")
        walk("toggle:void_drifter")
        press(A)
        assert "void_drifter" not in app.prefs.enabled
        press(A)
        assert "void_drifter" in app.prefs.enabled
        for pak in app.catalog.complete_ids():
            walk("solo:" + pak)
            press(A)
            assert app.route == "game" and app.world.solo == pak
            tick(100)  # Play through the actual new-run introduction.
            world = app.world
            before = world.player.pos.copy()
            pad.axis(0, 24000)
            pad.axis(1, -20000)
            pad.axis(5, 32767)
            pad.button(X, True)
            shot_count = len(fired)
            attacks = False
            for _ in range(12):
                tick()
                attacks |= bool(world.projectiles or world.effects or world.kills)
            assert world.player.pos.distance_to(before) > 1, pak
            assert attacks or len(fired) > shot_count, pak  # A valid shot can immediately hit cover.
            assert app.gamepads.poll().controls.special
            snapshot(pak)
            pad.neutral()
            tick()
            press(START)
            assert app.route == "pause"
            before_time = world.time
            tick(30)
            assert world.time == before_time
            snapshot("pause")
            press(START)
            assert app.route == "game"
            press(START)
            walk("abandon")
            press(A)
            assert app.route == "home"
            runs.append({"pak": pak, "analog_movement": True, "trigger_fire": True, "special": True, "pause_resume": True})
        walk("solo:signal_runner")
        press(A)
        tick(100)
        before_time = app.world.time
        pad.detach()
        tick()
        assert app.route == "pause" and app.world.time == before_time
        replacement = VirtualPad()
        pad = replacement
        pad.button(A, True)
        tick()  # Open the replacement before selecting the test device among other pads.
        app.gamepads.select(pad.identity)
        tick(12)
        assert app.route == "pause", "Reconnecting held confirm must not resume"
        pad.neutral()
        tick()
        press(START)
        assert app.route == "game", (app.route,physical_count,app.window_focused,app.gamepads.active_id,pad.identity,
                                      app.gamepads._armed,app.gamepads._previous,
                                      [(id,d.name,d.attached(),d.get_axis(0),d.get_axis(1),d.get_axis(5)) for id,d in app.gamepads.devices.items()])
        app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        pad.button(A, True)
        tick(12)
        assert app.route == "pause"
        app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
        tick()
        assert app.route == "pause"
        pad.neutral()
        tick()
        press(A)
        assert app.route == "game"
        app.world.player.health = 0  # Exercise the outcome UI without a balance-dependent wait.
        tick()
        assert app.route == "outcome"
        snapshot("outcome")
        tick()  # Observe neutral input on the new screen before confirming retry.
        press(A)
        assert app.route == "game" and app.world.solo == "signal_runner" and app.world.score == 0
        return {"native_sdl_virtual_controller": True, "physical_controllers_seen": physical_count,
                "gamepad_only_menu_paths": True, "preferences_saved": True, "nested_back": True,
                "pak_selection": True, "solo_inputs": runs, "disconnect_pauses": True,
                "reconnect_requires_neutral": True, "focus_loss_guard": True, "outcome_retry": True, "steps": steps}
    finally:
        app.audio.play_asset = original_play
        pad.detach()
        if replacement is not None: replacement.detach()
