"""Phase Garden: pilot behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import PilotBase


class PhaseGardenPilot(PilotBase):
    controls = 'Arrows / WASD: step-dash'
    special = 'X: blink through cover'

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
        if direction.length_squared():
            p.angle = math.atan2(direction.y, direction.x)
        if special:
            p.pos = world.safe_position(p.pos + unit(p.angle) * 160, 12)
            world.burst(p.pos, world.pak("pilot").color, 16)
        p.vel = direction * 235
        # Distinct step-dash rhythm, expressed in simulation seconds.
        if world.time % .20 < .13:
            world.move_body(p, p.vel * (dt * 1.54), 12)
