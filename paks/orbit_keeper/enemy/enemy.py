"""Orbit Keeper: local enemy state, spawn rules, contacts and death behavior."""
from dataclasses import dataclass
import math
from system_panic.model import Vec, WIDTH, HEIGHT, Enemy, normalized, unit
from system_panic.pak_api import EnemyBase
from .bullet import HostileShot


@dataclass
class Sentinel(Enemy):
    age: float = 0.
    timer: float = 0.


class OrbitKeeperEnemy(EnemyBase):
    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        return self.creatures

    def create(self, world, identity, position):
        health = 30 + world.wave * 3
        return Sentinel(id=identity, pos=Vec(position), health=health, max_health=health,
                          radius=14, timer=world.rng.uniform(.6, 2), angle=world.rng.uniform(0, math.tau))

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        toward = normalized(world.player.pos - enemy.pos)
        center = Vec(WIDTH / 2, HEIGHT / 2)
        enemy.angle += (.40 + world.wave * .02) * dt * (-1 if enemy.id % 2 else 1)
        radius = 90 + (enemy.id % 4) * 42
        target = center + unit(enemy.angle) * radius
        enemy.vel = (target - enemy.pos) * 1.5
        motion = world.move_body(enemy, enemy.vel * dt, enemy.radius)
        if motion.blocked_y:
            enemy.vel.y = 0
        if enemy.timer <= 0:
            enemy.timer = 2.7 / world.factor
            self.shoot(world, enemy, toward, 120)

    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle)

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
