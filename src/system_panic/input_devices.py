"""SDL-mapped controllers and device-neutral menu navigation; no Pak rules here."""
from __future__ import annotations

from dataclasses import dataclass, field
import math

import pygame

from .model import Controls

try:
    from pygame._sdl2 import controller as sdl_controller
except ImportError:  # Keyboard/mouse remain usable on builds without this SDL module.
    sdl_controller = None

A, B, X = pygame.CONTROLLER_BUTTON_A, pygame.CONTROLLER_BUTTON_B, pygame.CONTROLLER_BUTTON_X
START, BACK = pygame.CONTROLLER_BUTTON_START, pygame.CONTROLLER_BUTTON_BACK
LB, RB = pygame.CONTROLLER_BUTTON_LEFTSHOULDER, pygame.CONTROLLER_BUTTON_RIGHTSHOULDER
UP, DOWN = pygame.CONTROLLER_BUTTON_DPAD_UP, pygame.CONTROLLER_BUTTON_DPAD_DOWN
LEFT, RIGHT = pygame.CONTROLLER_BUTTON_DPAD_LEFT, pygame.CONTROLLER_BUTTON_DPAD_RIGHT
BUTTONS = (A, B, X, START, BACK, LB, RB, UP, DOWN, LEFT, RIGHT)


def stick(x: float, y: float, deadzone: float) -> tuple[float, float]:
    """Eight digital directions, matching the D-pad at every accepted deflection."""
    x = (1 if x > 0 else -1) if abs(x) > deadzone else 0
    y = (1 if y > 0 else -1) if abs(y) > deadzone else 0
    length = math.hypot(x, y)
    if not length:
        return 0., 0.
    return x / length, y / length


@dataclass
class PadFrame:
    controls: Controls = field(default_factory=Controls)
    pressed: frozenset[int] = frozenset()
    menu: tuple[float, float] = (0., 0.)
    activity: bool = False
    neutral: bool = True


@dataclass(frozen=True)
class DeviceNotice:
    text: str
    active_lost: bool = False


class Gamepads:
    """Keep device indices separate from stable SDL instance IDs; last used pad wins."""
    def __init__(self, backend=None):
        self.backend = backend if backend is not None else sdl_controller
        self.devices = {}
        self.active_id = None
        self.notices: list[DeviceNotice] = []
        self.error = ""
        self._armed = False
        self._previous = frozenset()
        self._last_axes = (0., 0.)
        self._last_fire = False
        if self.backend is not None:
            try:
                self.backend.init()
                for index in range(self.backend.get_count()):
                    self.open(index, announce=False)
            except pygame.error as exc:
                self.error = str(exc)

    @property
    def connected(self):
        return self.active_id in self.devices

    @property
    def name(self):
        return str(self.devices[self.active_id].name) if self.connected else "No compatible gamepad connected"

    def block(self):
        """Require a neutral frame after route/focus/device changes; never on Pak swaps."""
        self._armed = False

    def open(self, index, *, announce=True):
        try:
            if self.backend is None or not self.backend.is_controller(index):
                return
            device = self.backend.Controller(index)
            # Controller.id is an opening index, not SDL's hot-plug instance ID.
            identity = device.as_joystick().get_instance_id()
            if identity in self.devices:
                return
            self.devices[identity] = device
            if self.active_id is None:
                self.select(identity)
            if announce:
                self.notices.append(DeviceNotice(f"Gamepad connected: {device.name}"))
        except pygame.error as exc:
            self.error = str(exc)

    def select(self, instance_id):
        if instance_id in self.devices and self.active_id != instance_id:
            self.active_id = instance_id
            self._previous, self._last_axes, self._last_fire = frozenset(), (0., 0.), False
            self.block()

    def select_next(self):
        ids = list(self.devices)
        if ids:
            self.select(ids[(ids.index(self.active_id) + 1) % len(ids)])
        return self.name

    def remove(self, instance_id):
        device = self.devices.pop(instance_id, None)
        if device is None:
            return
        active = instance_id == self.active_id
        name = str(device.name)
        try:
            device.quit()
        except pygame.error:
            pass
        if active:
            self.active_id = None
            self.select(next(iter(self.devices), None))
            self.block()
        self.notices.append(DeviceNotice(f"Gamepad disconnected: {name}", active))

    def handle_event(self, event):
        if event.type == pygame.CONTROLLERDEVICEADDED:
            self.open(event.device_index)
        elif event.type == pygame.CONTROLLERDEVICEREMOVED:
            self.remove(event.instance_id)
        elif event.type == pygame.CONTROLLERDEVICEREMAPPED:
            if event.instance_id == self.active_id:
                self.block()
        elif event.type == pygame.CONTROLLERBUTTONDOWN:
            self.select(event.instance_id)
        elif event.type == pygame.CONTROLLERAXISMOTION:
            if event.axis in (pygame.CONTROLLER_AXIS_LEFTX, pygame.CONTROLLER_AXIS_LEFTY, pygame.CONTROLLER_AXIS_TRIGGERRIGHT) and abs(event.value) > 18000:
                self.select(event.instance_id)
        # Joystick duplicates are deliberately ignored: SDL supplies the physical mapping.

    def poll(self, deadzone=.18) -> PadFrame:
        if not self.connected:
            return PadFrame()
        device = self.devices[self.active_id]
        try:
            if not device.attached():
                self.remove(self.active_id)
                return PadFrame()
            buttons = frozenset(button for button in BUTTONS if device.get_button(button))
            axes = tuple(max(-1., min(1., device.get_axis(axis) / 32767.)) for axis in
                         (pygame.CONTROLLER_AXIS_LEFTX, pygame.CONTROLLER_AXIS_LEFTY))
            trigger = device.get_axis(pygame.CONTROLLER_AXIS_TRIGGERRIGHT) / 32767.
        except pygame.error:
            self.remove(self.active_id)
            return PadFrame()
        digital = (int(RIGHT in buttons) - int(LEFT in buttons), int(DOWN in buttons) - int(UP in buttons))
        movement = stick(*digital, 0.) if any(digital) else stick(*axes, deadzone)
        fire = A in buttons or trigger > .25
        special = X in buttons or LB in buttons
        pressed = buttons - self._previous
        activity = bool(pressed or fire != self._last_fire or (any(movement) and movement != self._last_axes))
        self._previous, self._last_axes, self._last_fire = buttons, movement, fire
        neutral = not buttons and not fire and movement == (0., 0.)
        if not self._armed:
            if neutral:
                self._armed = True
            return PadFrame(neutral=neutral)
        return PadFrame(Controls(*movement, fire, special), pressed, movement, activity, neutral)

    def gameplay(self, frame: PadFrame) -> Controls:
        # A menu command may have blocked input AFTER this frame was sampled.
        return frame.controls if self._armed else Controls()

    def drain_notices(self):
        notices, self.notices = self.notices, []
        return notices

    def close(self):
        for device in self.devices.values():
            try:
                device.quit()
            except pygame.error:
                pass
        self.devices.clear()
        self.active_id = None
        self.block()


class MenuRepeat:
    """Directional stick hysteresis and bounded repeat, separate from simulation time."""
    def __init__(self):
        self.direction = (0, 0)
        self.remaining = 0.
        self.blocked = False

    def block(self):
        self.direction, self.remaining, self.blocked = (0, 0), 0., True

    def update(self, x, y, elapsed):
        threshold = .35 if self.direction != (0, 0) else .55
        if max(abs(x), abs(y)) < threshold:
            self.direction, self.remaining, self.blocked = (0, 0), 0., False
            return None
        if self.blocked:
            return None
        direction = ((1 if x > 0 else -1), 0) if abs(x) > abs(y) else (0, (1 if y > 0 else -1))
        if direction != self.direction:
            self.direction, self.remaining = direction, .35
            return direction
        self.remaining -= max(0., elapsed)
        if self.remaining <= 0:
            self.remaining = .12
            return direction
        return None


def spatial_focus(rects, current, direction):
    """Nearest aligned target, wrapping to the opposite edge in the same lane."""
    if len(rects) < 2:
        return current
    dx, dy = direction
    origin = rects[current].center
    candidates, wrapped = [], []
    for index, rect in enumerate(rects):
        if index == current:
            continue
        x, y = rect.centerx - origin[0], rect.centery - origin[1]
        forward, across = x * dx + y * dy, abs(x * dy - y * dx)
        if forward > 1:
            candidates.append((across * 3 + forward, index))
        wrapped.append((across * 3 + forward, index))
    return min(candidates or wrapped)[1]
