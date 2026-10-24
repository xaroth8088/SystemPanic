"""Iron Circuit: local enemy state, spawn rules, contacts and death behavior."""
from dataclasses import dataclass
import math
from system_panic.model import Vec, Enemy, normalized
from system_panic.pak_api import EnemyBase
from .bullet import HostileShot


@dataclass
class Turret(Enemy):
    age: float = 0.
    timer: float = 0.


class IronCircuitEnemy(EnemyBase):
    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        return self.creatures

    def create(self, world, identity, position):
        health = 30 + world.wave * 3
        return Turret(id=identity, pos=Vec(position), health=health, max_health=health,
                          radius=14, timer=world.rng.uniform(.6, 2), angle=world.rng.uniform(0, math.tau))

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        toward = normalized(world.player.pos - enemy.pos)
        enemy.angle = math.atan2(toward.y, toward.x)
        if enemy.timer <= 0:
            enemy.timer = max(.8, 2.8 / world.factor - world.wave * .08)
            self.shoot(world, enemy, toward, 130 + world.wave * 5)

    def shoot(self, world, enemy, direction, speed):
        world.projectiles.append(HostileShot(enemy.pos + direction * (enemy.radius + 6), direction * speed))

    def on_contact(self, world, enemy, dt):
        world.hit_player(13 * world.factor)

    def take_damage(self, world, enemy, damage):
        applied = world.apply_damage(enemy, damage)
        if applied:
            world.burst(enemy.pos, world.pak("enemy").color, 2)
        return applied

    def on_death(self, world, enemy):
        world.score += 100
        world.burst(enemy.pos, world.pak("enemy").color, 9)
        world.events.append("impact")
