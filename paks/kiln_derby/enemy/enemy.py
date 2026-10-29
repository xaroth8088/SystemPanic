"""Kiln golems alternate a heavy running pursuit with a vented hot-ash attack."""
from dataclasses import dataclass
import math
from system_panic.model import Enemy, Vec, WIDTH, HEIGHT, normalized
from system_panic.pak_api import EnemyBase
from .ash import Ash


@dataclass
class KilnGolem(Enemy):
    age: float = 0.
    timer: float = 0.
    heading: object = None
    side: float = 1.


class Golems(EnemyBase):
    def init(self):
        self.art = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        actor=entity
        angle=actor.angle if actor is not None else 0.
        facing=int((angle+math.tau/16)%math.tau/(math.tau/8))
        phase=int((world.time if world is not None else 0)*8)%4
        return self.art.frame(phase*8+facing, columns=8, rows=4)

    def sprite_angle(self,world,entity):return 0.

    def sprite_flip_x(self,world,entity):return False



    def spawn_position(self, world):
        point = Vec(world.rng.uniform(45, WIDTH-45), world.rng.uniform(45, HEIGHT-45))
        return world.safe_position(point, 15, away_from=world.player.pos, clearance=230)

    def create(self, world, identity, position):
        health = 40 + world.wave * 4
        return KilnGolem(id=identity, pos=Vec(position), radius=15, health=health,
                            max_health=health, timer=world.rng.uniform(.4, 1.6),
                            heading=Vec(1, 0), side=1 if identity%2 else -1)

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        delta = world.player.pos - enemy.pos
        toward = normalized(delta)
        speed = (68 + min(75, world.wave * 2.2)) * {'relaxed': .8, 'standard': 1., 'intense': 1.2}.get(world.prefs.difficulty, 1.)
        if enemy.timer <= 0:
            enemy.timer = max(.9, 2.2 - world.wave*.025)
            enemy.heading = normalized(world.player.pos + world.player.vel*.18 - enemy.pos)
            if world.wave >= 3:
                world.projectiles.append(Ash(enemy.pos, enemy.heading, 8 + world.wave*.5))
        phase = enemy.timer
        desired = enemy.heading * speed * 1.8 if phase > 1.3 else (toward + Vec(-toward.y,toward.x)*enemy.side*.45) * speed
        enemy.vel = enemy.vel.lerp(desired, 1 - math.exp(-3.8*dt))
        motion = world.move_body(enemy, enemy.vel*dt, enemy.radius)
        if motion.normals:
            enemy.side *= -1
            for normal in motion.normals:
                world.move_body(enemy, Vec(-normal.y,normal.x)*enemy.side*speed*dt, enemy.radius)
        enemy.angle = math.atan2(enemy.vel.y, enemy.vel.x)

    def on_contact(self, world, enemy, dt):
        world.hit_player((12 + world.wave*.55) * {'relaxed':.8, 'standard':1., 'intense':1.3}.get(world.prefs.difficulty,1.))

    def on_death(self, world, enemy):
        world.score += 110
        world.events.append('impact')
        world.burst(enemy.pos, (255, 180, 105), 10)

    def on_level_complete(self, world):
        world.score += world.wave*230
