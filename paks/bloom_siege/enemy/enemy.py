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
        return (65+80*(1-math.exp(-(world.wave-1)/35)))*math.sqrt(self.factor(world))

    def contact_damage(self, world):
        return (13+.45*(world.wave-1)**.7)*self.factor(world)

    def create(self, world, identity, position):
        health=(64+3.2*(world.wave-1)**.8)*math.sqrt(self.factor(world))
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
        applied=world.apply_damage(enemy,damage*(1.35 if enemy.state=='recover' else 1.))
        if applied:world.burst(enemy.pos,world.pak('enemy').color,1)
        return applied

    def advance_enemy(self, world, enemy, dt):
        enemy.age+=dt;enemy.timer-=dt
        toward=normalized(world.player.pos-enemy.pos)
        if enemy.state=='seek':
            # Weevils remember a position rather than homing through their charge.
            tangent=Vec(-toward.y,toward.x)*math.sin(enemy.age*1.8+enemy.id)
            avoidance=Vec()
            for shot in world.projectiles:
                delta=enemy.pos-shot.pos
                if shot.alive and .01<delta.length_squared()<95**2 and shot.is_threat_to(world,enemy):
                    avoidance+=normalized(delta)*(1-delta.length()/95)*2.8
            enemy.vel=normalized(toward+tangent*.5+avoidance)*self.move_speed(world)
            if enemy.timer<=0:
                enemy.state,enemy.timer='windup',.6
                enemy.target=world.player.pos.copy()
        elif enemy.state=='windup':
            enemy.vel*=math.exp(-10*dt)
            if enemy.timer<=0:
                enemy.state,enemy.timer='charge',.65
                enemy.vel=normalized(enemy.target-enemy.pos)*(220+self.move_speed(world))
        elif enemy.state=='charge':
            if enemy.timer<=0:enemy.state,enemy.timer='recover',.6
        else:
            enemy.vel*=math.exp(-8*dt)
            if enemy.timer<=0:enemy.state,enemy.timer='seek',1.6/(1+world.wave*.01)
        motion=world.move_body(enemy,enemy.vel*dt,enemy.radius)
        if motion.normals and enemy.state=='charge':enemy.state,enemy.timer='recover',.6
