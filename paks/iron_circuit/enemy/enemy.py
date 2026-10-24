"""Iron Circuit: enemy behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import EnemyBase


class IronCircuitEnemy(EnemyBase):
    family = 'turret'
    splits = 0

    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        return self.creatures

    def advance_enemy(self, world, enemy, dt):
        toward = normalized(world.player.pos - enemy.pos)
        speed = (45 + world.wave * 3) * world.factor
        enemy.angle = math.atan2(toward.y, toward.x)
        if enemy.timer <= 0:
            enemy.timer = max(.8, 2.8 / world.factor - world.wave * .08)
            world.enemy_shot(enemy, toward, 130 + world.wave * 5)
            if enemy.elite:
                world.enemy_shot(enemy, toward.rotate_rad(.3), 140)
                world.enemy_shot(enemy, toward.rotate_rad(-.3), 140)
