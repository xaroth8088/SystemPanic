"""Phase Garden: local enemy state, spawn rules, contacts and death behavior."""
from dataclasses import dataclass
import math
from system_panic.model import Vec, Enemy, normalized, unit
from system_panic.pak_api import EnemyBase
from .bullet import HostileShot


@dataclass
class Phantom(Enemy):
    age: float = 0.
    timer: float = 0.


class PhaseGardenEnemy(EnemyBase):
    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        return self.creatures

    def create(self, world, identity, position):
        health = 30 + world.wave * 3
        return Phantom(id=identity, pos=Vec(position), health=health, max_health=health,
                          radius=14, timer=world.rng.uniform(.6, 2), angle=world.rng.uniform(0, math.tau))

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        toward = normalized(world.player.pos - enemy.pos)
        speed = (45 + world.wave * 3) * world.factor
        enemy.vel = toward * speed * .65
        motion = world.move_body(enemy, enemy.vel * dt, enemy.radius)
        if motion.blocked_y:
            enemy.vel.y = 0
        if enemy.timer <= 0:
            enemy.timer = world.rng.uniform(2.3, 3.8)
            destination = world.player.pos + unit(world.rng.uniform(0, math.tau)) * 175
            world.burst(enemy.pos, world.pak("enemy").color, 5)
            enemy.pos = world.safe_position(destination, enemy.radius, avoid_player=True)
            self.shoot(world, enemy, toward, 110)

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
