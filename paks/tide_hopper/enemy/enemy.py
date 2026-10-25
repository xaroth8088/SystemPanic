"""Tide Hopper: level-scaled opposition and its local state."""
from dataclasses import dataclass, field
import math
from system_panic.model import Enemy,Vec,WIDTH,HEIGHT,unit,normalized,circle_rect
from system_panic.pak_api import EnemyBase
from .tactics import difficulty,spawn_position,pursue

@dataclass
class TideHopperBody(Enemy):
    age: float = 0.
    timer: float = 1.
    lane: float = 240.

class TideHopperEnemy(EnemyBase):
    def init(self): self.art=self.load_asset("enemy_sheet.png")
    def sprite(self,world,entity=None): return self.art

    def spawn_position(self,world):
        return spawn_position(world)

    def create(self,world,identity,position):
        health=30+world.wave*3
        return TideHopperBody(id=identity,pos=Vec(position),health=health,max_health=health,radius=14,
                         angle=world.rng.uniform(0,math.tau),timer=world.rng.uniform(.8,2), lane=position.y)

    def move_speed(self,world):
        return (85+145*(1-math.exp(-(world.wave-1)/35)))*difficulty(world)

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        if enemy.timer<=0 and world.wave>=5:
            enemy.timer=max(.7,3./(1+.035*world.wave))
            # Later traffic changes lanes toward the predicted landing bank.
            enemy.lane=max(50,min(HEIGHT-50,round((world.player.pos.y+world.player.vel.y*.2)/60)*60))
        direction=-1 if enemy.id%2 else 1
        enemy.vel=Vec(direction*self.move_speed(world),max(-70,min(70,(enemy.lane-enemy.pos.y)*2)))
        previous=enemy.pos.copy()
        motion=world.move_body(enemy,enemy.vel*dt,enemy.radius,bounds=None)
        if motion.normals:
            # Traffic can break through a blocked road rather than park forever.
            for wall in world.cover:
                if circle_rect(previous+normalized(enemy.vel)*35,enemy.radius+4,wall.rect): world.hit_cover(wall,55*dt)
        enemy.pos.x%=WIDTH
        enemy.pos.y=max(enemy.radius,min(HEIGHT-enemy.radius,enemy.pos.y))

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
