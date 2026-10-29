"""Maze Muncher: level-scaled opposition and its local state."""
from dataclasses import dataclass, field
import math
from system_panic.model import Enemy,Vec,WIDTH,HEIGHT,unit,normalized,circle_rect
from system_panic.pak_api import EnemyBase
from .tactics import difficulty,spawn_position,pursue
from .navigation import Route,move,grid_position,delta

@dataclass
class MazeMuncherBody(Enemy):
    age: float = 0.
    timer: float = 1.
    stunned: float = 0.
    scattering: bool = False
    route: object = None
    route_time: float = 0.
    route_direction: object = None

class MazeMuncherEnemy(EnemyBase):
    def init(self):
        self.art=self.load_asset("enemy_sheet.png")
        self._graphs={}

    def on_level_start(self,world):self._graphs.clear()

    def on_shuffle(self,world,changed):self._graphs.clear()
    def sprite(self,world,entity=None):
        if entity is not None and (entity.stunned or entity.scattering):return self.art.frame(1 if entity.stunned else 3,columns=4)
        return self.art.frame(int((world.time if world else 0)*7+(entity.id if entity else 0))%4,columns=4)

    def spawn_position(self,world):
        desired=spawn_position(world)
        return grid_position(world,desired,Enemy(id=-1,pos=desired,radius=14))

    def create(self,world,identity,position):
        health=30+world.wave*3
        return MazeMuncherBody(id=identity,pos=Vec(position),health=health,max_health=health,radius=14,
                         angle=world.rng.uniform(0,math.tau),timer=world.rng.uniform(.8,2))

    def move_speed(self,world):
        return (65+115*(1-math.exp(-(world.wave-1)/35)))*difficulty(world)

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.stunned=max(0.,enemy.stunned-dt)
        if enemy.stunned:
            move(world,enemy,enemy.vel*dt,enemy.radius)
            enemy.vel*=max(0.,1-dt*8)
            return
        player=world.player
        # Distinct chase personalities alternate with a shorter scatter phase.
        period=max(4.,9.-world.wave*.06)
        enemy.scattering=enemy.age%period>period-1.6
        if enemy.scattering:
            target=(Vec(70,70),Vec(WIDTH-70,70),Vec(70,HEIGHT-70),Vec(WIDTH-70,HEIGHT-70))[enemy.id%4]
        elif enemy.id%3==0:
            target=player.pos+player.vel*min(.7,.12+world.wave*.02)
        elif enemy.id%3==1:
            target=player.pos+unit(player.angle+math.pi/2)*min(120,world.wave*6)
        else:
            target=player.pos
        if enemy.route is None:enemy.route=Route(True,self._graphs)
        enemy.route_time-=dt
        if enemy.route_time<=0:
            enemy.route_time=.05
            enemy.route.body=enemy
            enemy.route_direction=enemy.route.direction(world,target,enemy)
        enemy.vel=enemy.route_direction.normalize()*self.move_speed(world) if enemy.route_direction.length_squared() else Vec()
        # A corner turn finishes the small perpendicular alignment left by
        # finite fixed steps; the collision resolver still checks that motion.
        axis=1 if enemy.vel.x else 0
        center=16+round((enemy.pos[axis]-16)/32)*32
        if abs(enemy.pos[axis]-center)<=3.5:
            correction=Vec();correction[axis]=center-enemy.pos[axis]
            move(world,enemy,correction,enemy.radius)
        move(world,enemy,enemy.vel*dt,enemy.radius)
        enemy.angle=math.atan2(enemy.vel.y,enemy.vel.x)

    def sprite_angle(self,world,entity):return -math.degrees(entity.angle)

    def contact_damage(self,world):
        return (13+.6*(world.wave-1)**.7)*difficulty(world)

    def on_contact(self,world,enemy,dt):
        if not enemy.stunned:world.hit_player(self.contact_damage(world))

    def on_level_complete(self,world):
        world.score+=250*world.wave

    def on_death(self,world,enemy):
        world.score+=100
        world.burst(enemy.pos,world.pak("enemy").color,9)
        world.events.append("impact")

    def take_damage(self, world, enemy, damage):
        applied=world.apply_damage(enemy,damage)
        if applied:
            enemy.stunned=.2
            world.burst(enemy.pos,world.pak("enemy").color,2)
        return applied
