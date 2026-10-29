"""Storm moths tack across the wind and accelerate through their approach."""
from dataclasses import dataclass
import math
from system_panic.model import Enemy, Vec, WIDTH, HEIGHT, normalized
from system_panic.pak_api import EnemyBase


@dataclass
class StormMoth(Enemy):
    age: float = 0.
    tack: float = 1.


class Moths(EnemyBase):
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
        desired = Vec(world.rng.uniform(50, WIDTH - 50), world.rng.uniform(45, HEIGHT - 45))
        return world.safe_position(desired, 15, away_from=world.player.pos, clearance=230)

    def create(self, world, identity, position):
        health = 37 + world.wave * 3.5
        return StormMoth(id=identity, pos=Vec(position), radius=14, health=health,
                         max_health=health, tack=1 if identity % 2 else -1)

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        delta = world.player.pos - enemy.pos
        toward = normalized(delta)
        side = Vec(-toward.y, toward.x) * enemy.tack
        cycle = enemy.age % 2.7
        speed = (70 + min(70, world.wave * 2)) * {'relaxed': .8, 'standard': 1., 'intense': 1.22}.get(world.prefs.difficulty, 1.)
        direction = normalized(toward + side * (.7 if cycle < 1.7 else -.2))
        enemy.vel = enemy.vel.lerp(direction * speed * (1.65 if cycle > 2.1 else 1), 1 - math.exp(-4 * dt))
        motion = world.move_body(enemy, enemy.vel * dt, enemy.radius)
        if motion.normals:
            enemy.tack *= -1
            # Slide along contact instead of repeatedly driving into the hub.
            for normal in motion.normals:
                tangent = Vec(-normal.y, normal.x) * enemy.tack
                world.move_body(enemy, tangent * speed * dt, enemy.radius)
        enemy.angle = math.atan2(enemy.vel.y, enemy.vel.x)

    def on_contact(self, world, enemy, dt):
        world.hit_player((11 + world.wave * .6) * {'relaxed': .8, 'standard': 1., 'intense': 1.3}.get(world.prefs.difficulty, 1.))

    def on_death(self, world, enemy):
        world.score += 110
        world.events.append('impact')
        world.burst(enemy.pos, (175, 208, 255), 10)

    def on_level_complete(self, world):
        world.score += 220 * world.wave
