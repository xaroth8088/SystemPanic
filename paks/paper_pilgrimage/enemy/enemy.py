"""Paper mantises unfold to circle, then fold into a committed straight dart."""
from dataclasses import dataclass, field
import math
from system_panic.model import Enemy, Vec, WIDTH, HEIGHT, normalized
from system_panic.pak_api import EnemyBase


@dataclass
class Mantis(Enemy):
    age: float = 0.
    timer: float = 0.
    folded: bool = False
    heading: Vec = field(default_factory=lambda:Vec(1, 0))


class PaperEnemies(EnemyBase):
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
        return {'relaxed':.72, 'standard':1., 'intense':1.3}.get(world.prefs.difficulty, 1.)

    def spawn_position(self, world):
        return world.safe_position(Vec(world.rng.uniform(45, WIDTH-45), world.rng.uniform(45, HEIGHT-45)),
                                   14, away_from=world.player.pos, clearance=190)

    def create(self, world, identity, position):
        health = 25+3*world.wave
        return Mantis(pos=Vec(position), health=health, max_health=health, radius=14, id=identity,
                    timer=.6+world.rng.random()*1.2)

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        toward = normalized(world.player.pos-enemy.pos)
        if enemy.timer <= 0:
            enemy.folded = not enemy.folded
            if enemy.folded:
                enemy.heading = normalized(world.player.pos+world.player.vel*.16-enemy.pos)
                enemy.timer = .48
            else:
                enemy.timer = max(.8, 2.2/(1+.025*world.wave))
        if enemy.folded:
            enemy.vel = enemy.heading*(210+min(90, world.wave*3))*math.sqrt(self.factor(world))
        else:
            tangent = Vec(-toward.y, toward.x)*(1 if enemy.id%2 else -1)
            enemy.vel = normalized(toward+tangent*.6)*(65+min(60, world.wave*2))*math.sqrt(self.factor(world))
        motion = world.move_body(enemy, enemy.vel*dt, enemy.radius)
        if motion.normals:
            # A committed dart unfolds at a wall; its next target is chosen later.
            enemy.folded, enemy.timer = False, min(enemy.timer, .45)
            tangent = Vec(-toward.y, toward.x)*(1 if enemy.id%2 else -1)
            world.move_body(enemy, tangent*90*dt, enemy.radius)
        enemy.angle = math.atan2(enemy.vel.y, enemy.vel.x)

    def on_contact(self, world, enemy, dt):
        world.hit_player((12+.55*world.wave)*self.factor(world))

    def on_level_complete(self, world):
        world.score += 230*world.wave

    def on_death(self, world, enemy):
        world.score += 110
        world.burst(enemy.pos, world.pak('enemy').color, 9)
        world.events.append('impact')
