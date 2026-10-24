"""Void Drifter: local enemy state, spawn rules, contacts and death behavior."""
from dataclasses import dataclass
import math
from system_panic.model import Vec, WIDTH, HEIGHT, Enemy, normalized, unit
from system_panic.pak_api import EnemyBase


@dataclass
class Asteroid(Enemy):
    age: float = 0.
    timer: float = 0.
    fragment: bool = False


class VoidDrifterEnemy(EnemyBase):
    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        return self.creatures

    def create(self, world, identity, position):
        health = 30 + world.wave * 3
        return Asteroid(id=identity, pos=Vec(position), health=health, max_health=health,
                          radius=14, timer=world.rng.uniform(.6, 2), angle=world.rng.uniform(0, math.tau))

    def create_fragment(self, world, identity, position):
        enemy = self.create(world, identity, position)
        enemy.health *= .5
        enemy.max_health = enemy.health
        enemy.radius = 9
        enemy.fragment = True
        return enemy

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        toward = normalized(world.player.pos - enemy.pos)
        speed = (45 + world.wave * 3) * world.factor
        enemy.angle += .12 * dt
        enemy.vel = unit(enemy.angle) * speed * .8 + toward * speed * .3
        motion = world.move_body(enemy, enemy.vel * dt, enemy.radius, bounds=None)
        enemy.pos.x %= WIDTH
        enemy.pos.y %= HEIGHT
        if motion.blocked_y:
            enemy.vel.y = 0

    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle)

    def on_contact(self, world, enemy, dt):
        world.hit_player(13 * world.factor)

    def take_damage(self, world, enemy, damage):
        applied = world.apply_damage(enemy, damage)
        if applied:
            world.burst(enemy.pos, world.pak("enemy").color, 2)
        return applied

    def on_death(self, world, enemy):
        world.score += 60 if enemy.fragment else 100
        world.burst(enemy.pos, world.pak("enemy").color, 9)
        world.events.append("impact")
        if not enemy.fragment:
            for offset in (-18, 18):
                position = world.safe_position(enemy.pos + Vec(offset, offset), 9)
                world.spawn_enemy(position, factory=self.create_fragment)
