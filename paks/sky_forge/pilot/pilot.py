"""Sky Forge: pilot behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import PilotBase


class SkyForgePilot(PilotBase):
    controls = 'Left / right: run. Up: double jump'
    special = 'X: rising forge leap'

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
        if jump and p.jumps < 2:
            p.vel.y = -330
            p.jumps += 1
            p.grounded = False
            world.burst(p.pos + Vec(0, 10), world.pak("pilot").color, 6)
        if special:
            p.vel.y = -450
            p.jumps = 1
        p.vel.x = control.x * 220
        p.vel.y = min(460, p.vel.y + 820 * dt)
        if control.x:
            p.angle = 0 if control.x > 0 else math.pi
        world.move_body(p, p.vel * dt, 12)

    def demo_controls(self, world):
        p = world.player
        target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
        delta = target.pos - p.pos
        vector = normalized(delta)
        special = int(world.time * 3) % 11 == 0
        return Controls(vector.x if delta.length() > 180 else -vector.x, -1 if world.time % 1.2 < .15 else 0, True, special)

    def sprite_flip_x(self, world, entity):
        return math.cos(entity.angle) < 0
