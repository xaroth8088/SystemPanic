"""SkyForge: level-scaled AI, attacks, spawn policy and rewards belong here."""
from dataclasses import dataclass
import math
from system_panic.model import Vec, WIDTH, HEIGHT, Enemy, normalized, unit
from system_panic.pak_api import EnemyBase
from .tactics import difficulty, spawn_position, pursue


@dataclass
class Crawler(Enemy):
    age: float = 0.
    timer: float = 0.


class SkyForgeEnemy(EnemyBase):
    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        return self.creatures

    def spawn_position(self, world):
        return spawn_position(world)

    def create(self, world, identity, position):
        health = 30 + world.wave * 3
        return Crawler(id=identity, pos=Vec(position), health=health, max_health=health,
                      radius=14, timer=world.rng.uniform(.6, 2), angle=world.rng.uniform(0, math.tau))

    def move_speed(self, world):
        return (145 + 160 * (1 - math.exp(-(world.wave - 1) / 35))) * math.sqrt(difficulty(world))

    def dash_interval(self, world):
        return max(.48, 1.4 / (1 + .04 * (world.wave - 1)) / math.sqrt(difficulty(world)))

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        if enemy.timer <= 0:
            lead = min(.55, max(0, world.wave - 3) * .02)
            direction = normalized(world.player.pos + world.player.vel * lead - enemy.pos)
            # Probe at launch; later crawlers choose a route around nearby platforms.
            pursue(world, enemy, direction, self.move_speed(world), 0, avoid=world.wave >= 4)
            enemy.timer = self.dash_interval(world)
        enemy.vel *= math.exp(-1.8 * dt)
        motion = world.move_body(enemy, enemy.vel * dt, enemy.radius)
        if world.wave >= 6:
            for normal in motion.normals:
                if enemy.vel.dot(normal) < 0:
                    enemy.vel = enemy.vel.reflect(normal) * .8
        elif motion.blocked_y:
            enemy.vel.y = 0

    def contact_damage(self, world):
        return (13 + .6 * (world.wave - 1) ** .7) * difficulty(world)

    def on_contact(self, world, enemy, dt):
        world.hit_player(self.contact_damage(world))

    def on_level_complete(self, world):
        world.score += 250 * world.wave

    def take_damage(self, world, enemy, damage):
        applied = world.apply_damage(enemy, damage)
        if applied:
            world.burst(enemy.pos, world.pak("enemy").color, 2)
        return applied

    def on_death(self, world, enemy):
        world.score += 100
        world.burst(enemy.pos, world.pak("enemy").color, 9)
        world.events.append("impact")
