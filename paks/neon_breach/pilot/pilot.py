"""Neon Breach: raw-input movement and abilities belong to this component."""
import math
import pygame
from system_panic.model import Pilot, Vec, Controls, WIDTH, HEIGHT, unit, normalized, circle_rect
from system_panic.pak_api import PilotBase


class NeonBreachPilot(PilotBase):
    controls = 'Left / right: perimeter slide. Up / down: unused'
    special = 'X: magnetic corner burst'

    def init(self):
        self.art = self.load_asset("pilot_sheet.png")
        self.sound = self.load_asset("special.ogg")
        self._previous_special = False
        self._special_remaining = 0.
        self._distance = 0.
        self._edge_y = 0.
        self._boost = 0.

    def sprite(self, world, entity=None):
        return self.art

    def create(self, world, position):
        return Pilot(pos=Vec(position), health=100, max_health=100, radius=11, angle=-math.pi / 2)

    def on_level_start(self, world):
        if world.wave > 1:
            world.player.health = min(world.player.max_health, world.player.health + 15)
        world.player.invulnerable = max(world.player.invulnerable, 2.)

    def on_shuffle(self, world, changed):
        world.player.invulnerable = max(world.player.invulnerable, 1.5)

    def take_damage(self, world, damage):
        applied = world.apply_damage(world.player, damage)
        if applied:
            world.player.invulnerable = .9
            world.shake = 6
            world.events.append("hurt")
            world.burst(world.player.pos, (255,110,130), 14)
        return applied

    def on_death(self, world):
        world.burst(world.player.pos, world.pak("pilot").color, 35)

    def update(self, world, dt, control):
        self._special_remaining = max(0., self._special_remaining - dt)
        special = control.special and not self._previous_special and self._special_remaining <= 0
        self._previous_special = control.special
        if special:
            self._special_remaining = 2.8
            world.player.invulnerable = max(world.player.invulnerable, .65)
            self.sound.play(volume=.65)
        self.move(world, dt, control, special)

    def activate(self, world):
        p = world.player.pos
        self._distance = p.x - 24 if p.y < HEIGHT / 2 else (WIDTH - 48) + (HEIGHT - 48) + WIDTH - 24 - p.x

    def move(self, world, dt, control, special):
        w, h = WIDTH - 48, HEIGHT - 48
        self._boost = max(0., self._boost - dt)
        if special:
            self._boost = .5
            self._distance += 70
        self._distance = (self._distance + control.x * (560 if self._boost else 250) * dt) % (2 * (w + h))
        d = self._distance
        if d < w: target = Vec(24 + d, 24)
        elif d < w + h: target = Vec(WIDTH - 24, 24 + d - w)
        elif d < 2 * w + h: target = Vec(WIDTH - 24 - (d - w - h), HEIGHT - 24)
        else: target = Vec(24, HEIGHT - 24 - (d - 2 * w - h))
        previous = world.player.pos.copy()
        world.player.pos = world.safe_position(target, world.player.radius)
        world.player.vel = (world.player.pos - previous) / dt if dt else Vec()
        toward = Vec(WIDTH / 2, HEIGHT / 2) - world.player.pos
        world.player.angle = math.atan2(toward.y, toward.x)

    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle) - 90

    def demo_controls(self, world):
        return Controls(.85, 0, True, int(world.time * 3) % 11 == 0)
