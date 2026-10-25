"""IronCircuit: level-scaled AI, attacks, spawn policy and rewards belong here."""
from dataclasses import dataclass
import math
from system_panic.model import Vec, WIDTH, HEIGHT, Enemy, normalized, unit
from system_panic.pak_api import EnemyBase
from .tactics import difficulty, spawn_position, pursue
from .bullet import HostileShot


@dataclass
class Turret(Enemy):
    age: float = 0.
    timer: float = 0.
    volley: int = 0


class IronCircuitEnemy(EnemyBase):
    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        return self.creatures

    def spawn_position(self, world):
        return spawn_position(world)

    def create(self, world, identity, position):
        health = 30 + world.wave * 3
        return Turret(id=identity, pos=Vec(position), health=health, max_health=health,
                      radius=14, timer=world.rng.uniform(.6, 2), angle=world.rng.uniform(0, math.tau))

    def shot_speed(self, world):
        return (135 + 150 * (1 - math.exp(-(world.wave - 1) / 30))) * math.sqrt(difficulty(world))

    def fire_interval(self, world):
        return max(.65, 2.72 / (1 + .035 * (world.wave - 1)) / difficulty(world))

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        speed = self.shot_speed(world)
        travel = min(.65, enemy.pos.distance_to(world.player.pos) / speed)
        lead = travel * min(.75, max(0, world.wave - 3) * .035)
        toward = normalized(world.player.pos + world.player.vel * lead - enemy.pos)
        enemy.angle = math.atan2(toward.y, toward.x)
        if enemy.timer <= 0:
            enemy.timer = self.fire_interval(world)
            self.shoot(world, enemy, toward, speed)
            enemy.volley += 1
            # Telegraphable alternating fans appear only after the player has learned aim.
            if world.wave >= 8 and enemy.volley % 2 == 0:
                for offset in (-.16, .16):
                    self.shoot(world, enemy, toward.rotate_rad(offset), speed * .9)

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
