"""Maze Muncher: level-scaled opposition and its local state."""
from dataclasses import dataclass, field
import math
from system_panic.model import Enemy,Vec,WIDTH,HEIGHT,unit,normalized,circle_rect
from system_panic.pak_api import EnemyBase
from .tactics import difficulty,spawn_position,pursue

@dataclass
class MazeMuncherBody(Enemy):
    age: float = 0.
    timer: float = 1.

class MazeMuncherEnemy(EnemyBase):
    def init(self): self.art=self.load_asset("enemy_sheet.png")
    def sprite(self,world,entity=None): return self.art

    def spawn_position(self,world):
        return spawn_position(world)

    def create(self,world,identity,position):
        health=30+world.wave*3
        return MazeMuncherBody(id=identity,pos=Vec(position),health=health,max_health=health,radius=14,
                         angle=world.rng.uniform(0,math.tau),timer=world.rng.uniform(.8,2))

    def move_speed(self,world):
        return (65+115*(1-math.exp(-(world.wave-1)/35)))*difficulty(world)

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        player=world.player
        # Distinct chase personalities alternate with a shorter scatter phase.
        period=max(4.,9.-world.wave*.06)
        if enemy.age%period>period-1.6:
            target=(Vec(70,70),Vec(WIDTH-70,70),Vec(70,HEIGHT-70),Vec(WIDTH-70,HEIGHT-70))[enemy.id%4]
        elif enemy.id%3==0:
            target=player.pos+player.vel*min(.7,.12+world.wave*.02)
        elif enemy.id%3==1:
            target=player.pos+unit(player.angle+math.pi/2)*min(120,world.wave*6)
        else:
            target=player.pos
        pursue(world,enemy,normalized(target-enemy.pos),self.move_speed(world),dt,avoid=True)

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
