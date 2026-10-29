"""VoidDrifter: level-scaled AI, attacks, spawn policy and rewards belong here."""
from dataclasses import dataclass
import math
from system_panic.model import Vec, WIDTH, HEIGHT, Enemy, normalized, unit
from system_panic.pak_api import EnemyBase
from .tactics import difficulty, spawn_position, pursue


@dataclass
class Asteroid(Enemy):
    age: float = 0.
    timer: float = 0.
    fragment: bool = False


class VoidDrifterEnemy(EnemyBase):
    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        return self.creatures.frame(int((world.time if world else 0)*7+(entity.id if entity else 0))%4,columns=4)

    def spawn_position(self, world):
        return spawn_position(world)

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

    def move_speed(self, world):
        return (48 + 150 * (1 - math.exp(-(world.wave - 1) / 38))) * difficulty(world)

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.angle += (.12 + .25 * (1 - math.exp(-(world.wave - 1) / 30))) * dt
        lead = min(.6, max(0, world.wave - 4) * .02)
        toward = normalized(world.player.pos + world.player.vel * lead - enemy.pos)
        # Fragments become quicker hunters; intact rocks retain their drifting inertia.
        pursuit = .3 + .35 * (1 - math.exp(-(world.wave - 1) / 25))
        direction = unit(enemy.angle) * .8 + toward * pursuit
        speed = self.move_speed(world) * direction.length() * (1.15 if enemy.fragment else 1.)
        pursue(world, enemy, direction, speed, dt, avoid=world.wave >= 6, wrap=True)

    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle)

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
        world.score += 60 if enemy.fragment else 100
        world.burst(enemy.pos, world.pak("enemy").color, 9)
        world.events.append("impact")
        if not enemy.fragment:
            for offset in (-18, 18):
                position = world.safe_position(enemy.pos + Vec(offset, offset), 9)
                world.spawn_enemy(position, factory=self.create_fragment)
