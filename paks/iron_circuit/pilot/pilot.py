"""Iron Circuit: pilot behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import PilotBase


class IronCircuitPilot(PilotBase):
    controls = 'Left / right: steer. Up / down: speed'
    special = 'X: overdrive and ram'

    def init(self):
        self.spritesheet = self.load_asset('pilot_sheet.png')
        self.dash_sound = self.load_asset("special.ogg")

    def sprite(self, world, entity=None):
        return self.spritesheet

    def move(self, world, dt, control, jump, special):
        if special:
            self.dash_sound.play(volume=.7)
        p = world.player
        direction = Vec(control.x, control.y)
        if direction.length_squared() > 1:
            direction.normalize_ip()
        p.angle += control.x * 2.9 * dt
        speed = 190 - control.y * 75 + (190 if p.phase_timer > 0 else 0)
        p.vel = unit(p.angle) * speed
        old = p.pos.copy()
        world.move_body(p, p.vel * dt, 12)
        if p.pos.distance_to(old) < speed * dt * .35:
            p.angle += math.pi * .7

    def demo_controls(self, world):
        p = world.player
        target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
        delta = target.pos - p.pos
        vector = normalized(delta)
        special = int(world.time * 3) % 11 == 0
        return Controls(math.sin(world.time * .7) * .7, -.3, True, special)

    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle) - 90
