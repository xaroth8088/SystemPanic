"""Signal Runner: enemy behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import EnemyBase


class SignalRunnerEnemy(EnemyBase):
    family = 'swarm'
    splits = 0

    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        return self.creatures

    def advance_enemy(self, world, enemy, dt):
        toward = normalized(world.player.pos - enemy.pos)
        speed = (45 + world.wave * 3) * world.factor
        enemy.vel = toward.rotate_rad(math.sin(enemy.age * 2 + enemy.id) * .35) * speed * 1.2
        world.move_body(enemy, enemy.vel * dt, enemy.radius)
