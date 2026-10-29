"""Neon Breach: level-scaled opposition and its local state."""
from dataclasses import dataclass, field
import math
from system_panic.model import Enemy,Vec,WIDTH,HEIGHT,unit,normalized,circle_rect
from system_panic.pak_api import EnemyBase
from .tactics import difficulty,spawn_position,pursue
from .bullet import HostileShot

@dataclass
class NeonBreachBody(Enemy):
    age: float = 0.
    timer: float = 1.
    state: str = 'drift'
    target: object = None

class NeonBreachEnemy(EnemyBase):
    def init(self): self.art=self.load_asset("enemy_sheet.png")
    def sprite(self,world,entity=None): return self.art.frame(int((world.time if world else 0)*7+(entity.id if entity else 0))%4,columns=4)

    def spawn_position(self,world):
        return world.safe_position(Vec(world.rng.uniform(100,WIDTH-100),world.rng.uniform(65,220)),14,away_from=world.player.pos,clearance=160)

    def create(self,world,identity,position):
        health=30+world.wave*3
        return NeonBreachBody(id=identity,pos=Vec(position),health=health,max_health=health,radius=14,
                         angle=world.rng.uniform(0,math.tau),timer=world.rng.uniform(.8,2))

    def move_speed(self,world):
        return (32+65*(1-math.exp(-(world.wave-1)/35)))*difficulty(world)

    def fire_interval(self, world):
        return max(.9,2.8/(1+.035*(world.wave-1))/difficulty(world))

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        enemy.vel = Vec(math.sin(enemy.age*.8+enemy.id)*self.move_speed(world),8+world.wave*.2)
        world.move_body(enemy,enemy.vel*dt,enemy.radius)
        if enemy.pos.y>HEIGHT-65: enemy.pos.y=55
        if enemy.state=='drift' and enemy.timer<=0:
            lead=min(.45,max(0,world.wave-4)*.02)
            enemy.target=world.player.pos+world.player.vel*lead
            enemy.state,enemy.timer='aim',.55
        elif enemy.state=='aim' and enemy.timer<=0:
            direction=normalized(enemy.target-enemy.pos)
            self.shoot(world,enemy,direction,120+90*(1-math.exp(-(world.wave-1)/35)))
            enemy.state,enemy.timer='drift',self.fire_interval(world)

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

    def shoot(self,world,enemy,direction,speed):
        damage=(12+.5*(world.wave-1)**.7)*difficulty(world)
        world.projectiles.append(HostileShot(enemy.pos+direction*(enemy.radius+6),direction*speed,damage))
