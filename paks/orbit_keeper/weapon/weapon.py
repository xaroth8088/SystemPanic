"""Orbit Keeper: weapon behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import WeaponBase


class OrbitKeeperWeapon(WeaponBase):
    cooldown = 0.48

    def init(self):
        self.projectiles = self.load_asset('weapon_sheet.png')
        self.shot_sound = self.load_asset("shot.ogg")

    def sprite(self, world, entity=None):
        return self.projectiles

    def fire(self, world, direction):
        self.shot_sound.play(volume=.3)
        world.spawn_shot(direction, 'glaive', damage=28, speed=430, radius=7, pierce=6, return_after=.55)
