"""Phase Garden: weapon behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import WeaponBase


class PhaseGardenWeapon(WeaponBase):
    cooldown = 0.58

    def init(self):
        self.projectiles = self.load_asset('weapon_sheet.png')
        self.shot_sound = self.load_asset("shot.ogg")

    def sprite(self, world, entity=None):
        return self.projectiles

    def fire(self, world, direction):
        self.shot_sound.play(volume=.3)
        remaining = [enemy for enemy in world.enemies if enemy.health > 0]
        start = world.player.pos.copy()
        for _ in range(4):
            if not remaining:
                break
            target = min(remaining, key=lambda enemy: enemy.pos.distance_squared_to(start))
            world.beams.append(Beam(start, target.pos.copy()))
            world.damage_enemy(target, 26)
            start = target.pos.copy()
            remaining.remove(target)
        for wall in world.cover:
            if circle_rect(world.player.pos, 150, wall.rect):
                wall.health -= 15
