"""Pak-owned enemy state machines, local difficulty, telegraphs and rewards."""
from dataclasses import dataclass, field
import math
import pygame
from system_panic.model import Enemy, Vec, WIDTH, HEIGHT, normalized, unit
from system_panic.pak_api import EnemyBase, ProjectileBase
from .hazards import Bolt, Zone


@dataclass
class Foe(Enemy):
    age: float = 0.
    timer: float = 0.
    state: str = 'seek'
    target: Vec = field(default_factory=Vec)
    attacks: int = 0


class Enemies(EnemyBase):
    def init(self):
        self.art=self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        age=entity.age if entity is not None else 0
        return self.art.frame(int(age*8)%4,columns=4)

    def spawn_position(self, world):
        for _ in range(24):
            point=Vec(world.rng.uniform(45,WIDTH-45),world.rng.uniform(45,HEIGHT-45))
            if point.distance_to(world.player.pos)>225:
                return world.safe_position(point,15,away_from=world.player.pos,clearance=200)
        return world.safe_position(Vec(WIDTH-70,70),15,away_from=world.player.pos,clearance=150)

    def factor(self, world):
        return {'relaxed':.7,'standard':1.,'intense':1.3}[world.prefs.difficulty]

    def move_speed(self, world):
        return (68+65*(1-math.exp(-(world.wave-1)/35)))*math.sqrt(self.factor(world))

    def contact_damage(self, world):
        return (13+.45*(world.wave-1)**.7)*self.factor(world)

    def create(self, world, identity, position):
        health=(54+3.2*(world.wave-1)**.8)*math.sqrt(self.factor(world))
        return Foe(id=identity,pos=Vec(position),radius=14,health=health,max_health=health,
                   timer=world.rng.uniform(.7,1.8),angle=world.rng.uniform(0,math.tau))



    def on_contact(self, world, enemy, dt):
        world.hit_player(self.contact_damage(world))
        delta=normalized(world.player.pos-enemy.pos)
        world.move_body(world.player,delta*12,world.player.radius)

    def on_death(self, world, enemy):
        world.score+=120+world.wave*3
        world.burst(enemy.pos,world.pak('enemy').color,14)
        world.events.append('impact')

    def on_level_complete(self, world):
        world.score+=200*world.wave

    def take_damage(self, world, enemy, damage):
        applied=world.apply_damage(enemy,damage*(1.4 if enemy.state=='recover' else 1.))
        if applied:world.burst(enemy.pos,world.pak('enemy').color,1)
        return applied

    def advance_enemy(self, world, enemy, dt):
        enemy.age+=dt
        enemy.timer-=dt
        if enemy.state=='seek':
            toward=normalized(world.player.pos-enemy.pos)
            enemy.vel=toward*self.move_speed(world)
            if enemy.timer<=0:
                enemy.state,enemy.timer='windup',.48
                enemy.target=world.player.pos.copy()
        elif enemy.state=='windup':
            enemy.vel*=math.exp(-12*dt)
            if enemy.timer<=0:
                enemy.state,enemy.timer='charge',.5
                enemy.vel=normalized(enemy.target-enemy.pos)*(310+self.move_speed(world))
                enemy.attacks+=1
                if world.wave>=4:
                    aim=normalized(enemy.target-enemy.pos)
                    world.projectiles.append(Bolt(enemy.pos+aim*20,aim*170,self.contact_damage(world)*.8))
        elif enemy.state=='charge':
            if enemy.timer<=0:
                enemy.state,enemy.timer='recover',.75
        else:
            enemy.vel*=math.exp(-7*dt)
            if enemy.timer<=0:
                enemy.state,enemy.timer='seek',max(.65,1.8-world.wave*.012)
                if world.wave>=6 and enemy.attacks%2==0:
                    world.projectiles.append(Zone(enemy.pos,65,.65,self.contact_damage(world)))
        motion=world.move_body(enemy,enemy.vel*dt,enemy.radius)
        if motion.normals and enemy.state=='charge':enemy.state,enemy.timer='recover',.75
