"""OrbitKeeper: level-scaled AI, attacks, spawn policy and rewards belong here."""
from dataclasses import dataclass
import math
from system_panic.model import Vec, WIDTH, HEIGHT, Enemy, normalized, unit
from system_panic.pak_api import EnemyBase
from .tactics import difficulty, spawn_position, pursue
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

    def spawn_position(self, world):
        return spawn_position(world)

    def create(self, world, identity, position):
        health = 30 + world.wave * 3
        return Sentinel(id=identity, pos=Vec(position), health=health, max_health=health,
                      radius=14, timer=world.rng.uniform(.6, 2), angle=world.rng.uniform(0, math.tau))

    def orbit_speed(self, world):
        return (.42 + .85 * (1 - math.exp(-(world.wave - 1) / 38))) * math.sqrt(difficulty(world))

    def fire_interval(self, world):
        return max(.8, 2.7 / (1 + .028 * (world.wave - 1)) / difficulty(world))

    def shot_speed(self, world):
        return (120 + 140 * (1 - math.exp(-(world.wave - 1) / 35))) * math.sqrt(difficulty(world))

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        center = Vec(WIDTH / 2, HEIGHT / 2)
        # Advanced sentinels shift their formation toward the pilot, closing safe pockets.
        center = center.lerp(world.player.pos, .45 * (1 - math.exp(-(world.wave - 1) / 30)))
        enemy.angle += self.orbit_speed(world) * dt * (-1 if enemy.id % 2 else 1)
        radius = 90 + (enemy.id % 4) * 42
        target = center + unit(enemy.angle) * radius
        delta = target - enemy.pos
        speed = min(120 + 80 * (1 - math.exp(-(world.wave - 1) / 40)), delta.length() * 1.5)
        pursue(world, enemy, normalized(delta), speed, dt, avoid=world.wave >= 5)
        if enemy.timer <= 0:
            enemy.timer = self.fire_interval(world)
            lead = min(.5, max(0, world.wave - 4) * .018)
            toward = normalized(world.player.pos + world.player.vel * lead - enemy.pos)
            self.shoot(world, enemy, toward, self.shot_speed(world))

    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle)

    def shoot(self, world, enemy, direction, speed):
        damage = (12 + .5 * (world.wave - 1) ** .7) * difficulty(world)
        world.projectiles.append(HostileShot(enemy.pos + direction * (enemy.radius + 6), direction * speed, damage))

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
