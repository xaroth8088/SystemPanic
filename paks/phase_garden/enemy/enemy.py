"""Phase Garden: enemy behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import EnemyBase


class PhaseGardenEnemy(EnemyBase):
    family = 'phantom'
    splits = 0

    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        return self.creatures

    def advance_enemy(self, world, enemy, dt):
        toward = normalized(world.player.pos - enemy.pos)
        speed = (45 + world.wave * 3) * world.factor
        enemy.vel = toward * speed * .65
        world.move_body(enemy, enemy.vel * dt, enemy.radius)
        if enemy.timer <= 0:
            enemy.timer = world.rng.uniform(2.3, 3.8)
            destination = world.player.pos + unit(world.rng.uniform(0, math.tau)) * 175
            world.burst(enemy.pos, world.pak("enemy").color, 5)
            enemy.pos = world.safe_position(destination, enemy.radius, avoid_player=True)
            world.enemy_shot(enemy, toward, 110)
