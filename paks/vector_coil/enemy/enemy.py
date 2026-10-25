"""Vector Coil: level-scaled opposition and its local state."""
from dataclasses import dataclass, field
import math
from system_panic.model import Enemy,Vec,WIDTH,HEIGHT,unit,normalized,circle_rect
from system_panic.pak_api import EnemyBase
from .tactics import difficulty,spawn_position,pursue

@dataclass
class VectorCoilBody(Enemy):
    age: float = 0.
    timer: float = 1.

class VectorCoilEnemy(EnemyBase):
    def init(self): self.art=self.load_asset("enemy_sheet.png")
    def sprite(self,world,entity=None): return self.art

    def spawn_position(self,world):
        return spawn_position(world)

    def create(self,world,identity,position):
        health=30+world.wave*3
        return VectorCoilBody(id=identity,pos=Vec(position),health=health,max_health=health,radius=14,
                         angle=world.rng.uniform(0,math.tau),timer=world.rng.uniform(.8,2))

    def move_speed(self,world):
        return (95+125*(1-math.exp(-(world.wave-1)/35)))*difficulty(world)

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        if enemy.vel.length_squared()<1:
            enemy.vel=unit(enemy.angle)*self.move_speed(world)
        if enemy.timer<=0:
            enemy.timer=max(.5,2.1/(1+.04*world.wave))
            pursuit=min(.7,.12+world.wave*.02)
            target=normalized(world.player.pos+world.player.vel*.2-enemy.pos)
            direction=normalized(enemy.vel).lerp(target,pursuit)
            enemy.vel=normalized(direction)*self.move_speed(world)
        motion=world.move_body(enemy,enemy.vel*dt,enemy.radius)
        for normal in motion.normals:
            if enemy.vel.dot(normal)<0: enemy.vel=enemy.vel.reflect(normal)
        enemy.angle=math.atan2(enemy.vel.y,enemy.vel.x)

    def contact_damage(self,world):
        return (13+.6*(world.wave-1)**.7)*difficulty(world)

    def on_contact(self,world,enemy,dt):
        world.hit_player(self.contact_damage(world))

    def on_level_complete(self,world):
        world.score+=250*world.wave

    def on_death(self,world,enemy):
        world.score+=100
        world.burst(enemy.pos,world.pak("enemy").color,9)
        world.events.append("impact")

    def take_damage(self, world, enemy, damage):
        applied=world.apply_damage(enemy,damage)
        if applied: world.burst(enemy.pos,world.pak("enemy").color,2)
        return applied
