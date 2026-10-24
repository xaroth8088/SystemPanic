"""Signal Runner: weapon behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import WeaponBase


class SignalRunnerWeapon(WeaponBase):
    cooldown = 0.14

    def init(self):
        self.projectiles = self.load_asset('weapon_sheet.png')
        self.shot_sound = self.load_asset("shot.ogg")

    def sprite(self, world, entity=None):
        return self.projectiles

    def fire(self, world, direction):
        self.shot_sound.play(volume=.3)
        world.spawn_shot(direction, 'pulse', damage=16, speed=520)
