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
        return (75+60*(1-math.exp(-(world.wave-1)/35)))*math.sqrt(self.factor(world))

    def contact_damage(self, world):
        return (13+.45*(world.wave-1)**.7)*self.factor(world)

    def create(self, world, identity, position):
        health=(44+3.2*(world.wave-1)**.8)*math.sqrt(self.factor(world))
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
        applied=world.apply_damage(enemy,damage*(.24 if enemy.state=='shield' else 1.25))
        if applied:world.burst(enemy.pos,world.pak('enemy').color,1)
        return applied

    def advance_enemy(self, world, enemy, dt):
        enemy.age+=dt;enemy.timer-=dt
        toward=normalized(world.player.pos-enemy.pos)
        distance=enemy.pos.distance_to(world.player.pos)
        tangent=Vec(-toward.y,toward.x)*(1 if enemy.id%2 else -1)
        enemy.state='shield' if enemy.age%3.2<1.7 else 'recover'
        direction=toward*(1 if distance>240 else -.45)+tangent*.75
        # Complete the skating arc along the perimeter instead of trying to
        # retreat forever into a corner behind a mirror.
        if enemy.pos.x<50:direction.x=1
        if enemy.pos.x>WIDTH-50:direction.x=-1
        if enemy.pos.y<50:direction.y=1
        if enemy.pos.y>HEIGHT-50:direction.y=-1
        enemy.vel=normalized(direction)*self.move_speed(world)
        world.move_body(enemy,enemy.vel*dt,enemy.radius)
        if enemy.timer<=0:
            prediction=world.player.pos+world.player.vel*min(.5,world.wave*.025)
            aim=normalized(prediction-enemy.pos)
            for angle in ((-.12,0,.12) if world.wave>=7 else (0,)):
                world.projectiles.append(Bolt(enemy.pos+aim*20,aim.rotate_rad(angle)*180,self.contact_damage(world)))
            enemy.timer=max(.85,2.8/(1+world.wave*.025))
