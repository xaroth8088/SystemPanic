"""Sky Forge: enemy behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import EnemyBase


class SkyForgeEnemy(EnemyBase):
    family = 'hopper'
    splits = 0

    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        return self.creatures

    def advance_enemy(self, world, enemy, dt):
        toward = normalized(world.player.pos - enemy.pos)
        speed = (45 + world.wave * 3) * world.factor
        if enemy.timer <= 0:
            enemy.vel = toward * 145
            enemy.timer = 1.4
        enemy.vel *= math.exp(-1.8 * dt)
        world.move_body(enemy, enemy.vel * dt, enemy.radius)
