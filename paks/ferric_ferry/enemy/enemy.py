"""Rivet skiffs make broad interception arcs and bounce off solid scenery."""
from dataclasses import dataclass
import math
from system_panic.model import Enemy, Vec, WIDTH, HEIGHT, normalized
from system_panic.pak_api import EnemyBase


@dataclass
class Skiff(Enemy):
    age: float = 0.
    bank: int = 1


class FerricEnemies(EnemyBase):
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


    def factor(self, world):
        return {'relaxed':.7, 'standard':1., 'intense':1.35}.get(world.prefs.difficulty, 1.)

    def spawn_position(self, world):
        return world.safe_position(Vec(world.rng.uniform(40, WIDTH-40), world.rng.uniform(40, HEIGHT-40)),
                                   15, away_from=world.player.pos, clearance=200)

    def create(self, world, identity, position):
        health = 32+3.5*world.wave
        return Skiff(pos=Vec(position), health=health, max_health=health, radius=15, id=identity,
                     bank=1 if identity%2 else -1)

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        lead = min(.3, .02*max(0, world.wave-2))
        toward = normalized(world.player.pos+world.player.vel*lead-enemy.pos)
        tangent = Vec(-toward.y, toward.x)*enemy.bank
        direction = normalized(toward+tangent*(.7+.35*math.sin(enemy.age*1.5)))
        desired = direction*(78+min(75, world.wave*2.5))*math.sqrt(self.factor(world))
        enemy.vel = enemy.vel.lerp(desired, 1-math.exp(-3*dt))
        motion = world.move_body(enemy, enemy.vel*dt, enemy.radius)
        if motion.normals:
            for normal in motion.normals:
                if enemy.vel.dot(normal) < 0: enemy.vel -= normal*enemy.vel.dot(normal)*1.6
            enemy.bank *= -1
            world.move_body(enemy, tangent*70*dt, enemy.radius)
        if enemy.vel.length_squared(): enemy.angle = math.atan2(enemy.vel.y, enemy.vel.x)

    def on_contact(self, world, enemy, dt):
        world.hit_player((14+.6*world.wave)*self.factor(world))

    def on_level_complete(self, world):
        world.score += 240*world.wave

    def on_death(self, world, enemy):
        world.score += 120
        world.burst(enemy.pos, world.pak('enemy').color, 10)
        world.events.append('impact')
