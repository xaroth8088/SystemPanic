"""Tide Hopper: level-scaled opposition and its local state."""
from dataclasses import dataclass, field
import math
from system_panic.model import Enemy,Vec,WIDTH,HEIGHT,unit,normalized,circle_rect
from system_panic.pak_api import EnemyBase
from .tactics import difficulty,spawn_position,pursue
from .grid import nearest,clear,delta

@dataclass
class TideHopperBody(Enemy):
    age: float = 0.
    timer: float = 1.
    lane: float = 240.
    landing: object = None
    last_position: object = None

class TideHopperEnemy(EnemyBase):
    def init(self): self.art=self.load_asset("enemy_sheet.png")
    def sprite(self,world,entity=None): return self.art.frame(int((world.time if world else 0)*7+(entity.id if entity else 0))%4,columns=4)

    def spawn_position(self,world):
        desired=spawn_position(world)
        return nearest(world,Enemy(pos=desired,radius=14),desired)

    def create(self,world,identity,position):
        health=30+world.wave*3
        return TideHopperBody(id=identity,pos=Vec(position),health=health,max_health=health,radius=14,
                         angle=0 if identity%2==0 else math.pi,timer=world.rng.uniform(.1,.4),lane=position.y)

    def move_speed(self,world):
        return (85+145*(1-math.exp(-(world.wave-1)/35)))*difficulty(world)

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        # Other weapons may move this public body. Yield while that continues,
        # then travel back to a clear lattice point instead of snapping it back.
        if enemy.last_position is not None and enemy.pos.distance_to(enemy.last_position)>.05:
            enemy.landing=None;enemy.timer=.2;enemy.last_position=enemy.pos.copy()
            return
        enemy.timer -= dt
        if enemy.landing is None and enemy.timer<=0:
            origin=nearest(world,enemy,enemy.pos)
            if delta(enemy.pos,origin).length()>1:enemy.landing=origin
            else:
                direction=-1 if enemy.id%2 else 1
                steps=[Vec(direction*48,0),Vec(0,48),Vec(0,-48),Vec(-direction*48,0)]
                if world.wave>=5 and int(enemy.age*2+enemy.id)%4==0:
                    steps.sort(key=lambda d:abs(origin.y+d.y-world.player.pos.y))
                for step in steps:
                    target=origin+step;target.x%=WIDTH
                    if not 14<=target.y<=HEIGHT-14 or not clear(world,enemy,target):continue
                    # Test intermediate points through actual filtered geometry.
                    travel=delta(origin,target)
                    if all(clear(world,enemy,(origin+travel*(i/8)).elementwise()%Vec(WIDTH,HEIGHT)) for i in range(1,9)):
                        enemy.landing=target;break
        enemy.vel=Vec()
        if enemy.landing is not None:
            travel=delta(enemy.pos,enemy.landing);distance=travel.length();speed=max(280.,min(550.,self.move_speed(world)*3.5))
            if distance>0:
                enemy.vel=travel.normalize()*speed;enemy.angle=math.atan2(travel.y,travel.x)
                motion=world.move_body(enemy,travel.normalize()*min(distance,speed*dt),enemy.radius,bounds=None)
                enemy.pos.x%=WIDTH
                if distance<=speed*dt and not motion.normals:enemy.pos=enemy.landing.copy()
                if distance<=speed*dt or motion.normals:
                    enemy.landing=None;enemy.timer=max(.08,48/self.move_speed(world)-48/speed)
        enemy.last_position=enemy.pos.copy()

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
