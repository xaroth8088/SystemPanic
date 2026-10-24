"""Signal Runner: pilot behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import PilotBase


class SignalRunnerPilot(PilotBase):
    controls = 'Arrows / WASD: strafe'
    special = 'X: dash through danger'

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
        p.vel = direction * (640 if p.phase_timer > 0 else 220)
        if direction.length_squared():
            p.angle = math.atan2(direction.y, direction.x)
        world.move_body(p, p.vel * dt, 12)
