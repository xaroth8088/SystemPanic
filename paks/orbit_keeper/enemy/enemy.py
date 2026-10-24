"""Orbit Keeper: enemy behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import EnemyBase


class OrbitKeeperEnemy(EnemyBase):
    family = 'sentinel'
    splits = 0

    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        return self.creatures

    def advance_enemy(self, world, enemy, dt):
        toward = normalized(world.player.pos - enemy.pos)
        speed = (45 + world.wave * 3) * world.factor
        center = Vec(WIDTH / 2, HEIGHT / 2)
        enemy.angle += (.40 + world.wave * .02) * dt * (-1 if enemy.id % 2 else 1)
        radius = 90 + (enemy.id % 4) * 42
        target = center + unit(enemy.angle) * radius
        enemy.vel = (target - enemy.pos) * 1.5
        world.move_body(enemy, enemy.vel * dt, enemy.radius)
        if enemy.timer <= 0:
            enemy.timer = 2.7 / world.factor
            world.enemy_shot(enemy, toward, 120)

    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle)
