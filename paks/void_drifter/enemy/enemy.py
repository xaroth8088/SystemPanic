"""Void Drifter: enemy behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import EnemyBase


class VoidDrifterEnemy(EnemyBase):
    family = 'asteroid'
    splits = 2

    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        return self.creatures

    def advance_enemy(self, world, enemy, dt):
        toward = normalized(world.player.pos - enemy.pos)
        speed = (45 + world.wave * 3) * world.factor
        enemy.angle += .12 * dt
        enemy.vel = unit(enemy.angle) * speed * .8 + toward * speed * .3
        world.move_body(enemy, enemy.vel * dt, enemy.radius, wrap=True)

    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle)
