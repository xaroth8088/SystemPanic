"""Sky Forge: weapon behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import WeaponBase


class SkyForgeWeapon(WeaponBase):
    cooldown = 0.6

    def init(self):
        self.projectiles = self.load_asset('weapon_sheet.png')
        self.shot_sound = self.load_asset("shot.ogg")

    def sprite(self, world, entity=None):
        return self.projectiles

    def fire(self, world, direction):
        self.shot_sound.play(volume=.3)
        world.spawn_shot(direction, 'bomb', damage=58, speed=380, radius=7, homing=2.2, blast=85)
