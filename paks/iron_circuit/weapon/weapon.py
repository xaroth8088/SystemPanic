"""Iron Circuit: weapon behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import WeaponBase


class IronCircuitWeapon(WeaponBase):
    cooldown = 0.45

    def init(self):
        self.projectiles = self.load_asset('weapon_sheet.png')
        self.shot_sound = self.load_asset("shot.ogg")

    def sprite(self, world, entity=None):
        return self.projectiles

    def fire(self, world, direction):
        self.shot_sound.play(volume=.3)
        for offset in (-.20, 0, .20):
            world.spawn_shot(direction.rotate_rad(offset), 'scatter', damage=19, speed=440, bounce=4)
