"""PhaseGarden: level-scaled AI, attacks, spawn policy and rewards belong here."""
from dataclasses import dataclass
import math
from system_panic.model import Vec, WIDTH, HEIGHT, Enemy, normalized, unit
from system_panic.pak_api import EnemyBase
from .tactics import difficulty, spawn_position, pursue
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

    def spawn_position(self, world):
        return spawn_position(world)

    def create(self, world, identity, position):
        health = 30 + world.wave * 3
        return Phantom(id=identity, pos=Vec(position), health=health, max_health=health,
                      radius=14, timer=world.rng.uniform(.6, 2), angle=world.rng.uniform(0, math.tau))

    def move_speed(self, world):
        return (48 + 120 * (1 - math.exp(-(world.wave - 1) / 32))) * difficulty(world) * .65

    def teleport_interval(self, world):
        return max(1., 3.05 / (1 + .035 * (world.wave - 1)) / math.sqrt(difficulty(world)))

    def shot_speed(self, world):
        return (110 + 135 * (1 - math.exp(-(world.wave - 1) / 35))) * math.sqrt(difficulty(world))

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        toward = normalized(world.player.pos - enemy.pos)
        pursue(world, enemy, toward, self.move_speed(world), dt, avoid=world.wave >= 5)
        if enemy.timer <= 0:
            enemy.timer = self.teleport_interval(world) * world.rng.uniform(.85, 1.15)
            lead = min(.5, max(0, world.wave - 4) * .02)
            radius = 100 + 75 * math.exp(-(world.wave - 1) / 35)
            predicted = world.player.pos + world.player.vel * lead
            destination = predicted + unit(world.rng.uniform(0, math.tau)) * radius
            world.burst(enemy.pos, world.pak("enemy").color, 5)
            enemy.pos = world.safe_position(destination, enemy.radius, away_from=world.player.pos, clearance=100)
            # Re-aim AFTER relocation; using the old vector would fire away from the pilot.
            direction = normalized(predicted - enemy.pos)
            self.shoot(world, enemy, direction, self.shot_speed(world))

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
