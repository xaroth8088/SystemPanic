"""Void Drifter: pilot behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import PilotBase


class VoidDrifterPilot(PilotBase):
    controls = 'Left / right: turn. Up: thrust'
    special = 'X: brake and reverse thrust'

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
        p.angle += control.x * 3.7 * dt
        p.vel += unit(p.angle) * (-control.y) * 360 * dt
        p.vel *= math.exp(-.22 * dt)
        if special:
            p.vel *= -.25
        if p.vel.length() > 330:
            p.vel.scale_to_length(330)
        world.move_body(p, p.vel * dt, 12, wrap=True)

    def demo_controls(self, world):
        p = world.player
        target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
        delta = target.pos - p.pos
        vector = normalized(delta)
        special = int(world.time * 3) % 11 == 0
        angle = math.atan2(delta.y, delta.x)
        diff = (angle - p.angle + math.pi) % math.tau - math.pi
        return Controls(max(-1, min(1, diff * 2)), -1 if delta.length() > 180 else .3, True, special)

    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle) - 90
