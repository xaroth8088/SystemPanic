"""Accelerating pinball with local bounce, paddle reflection and hit clocks."""
import math
import pygame
from system_panic.model import Vec,WIDTH,HEIGHT,normalized,circle_rect
from system_panic.pak_api import ProjectileBase

class PlasmaBall(ProjectileBase):
    def __init__(self,world,weapon,direction):
        super().__init__(world.player.pos+direction*24,direction*420,8)
        self.weapon=weapon
        self.remaining=10.
        self.hits={}
        self.guided=world.prefs.aim_assist and world.component("pilot").aim_direction(world) is None

    def update(self,world,dt):
        self.remaining-=dt
        self.hits={id:time-dt for id,time in self.hits.items() if time>dt}
        if self.remaining<=0:
            self.alive=False
            return
        speed=self.vel.length()
        targets=[e for e in world.enemies if e.health>0]
        if self.guided and targets:
            target=min(targets,key=lambda e:e.pos.distance_squared_to(self.pos))
            direction=normalized(target.pos-self.pos)
            turn=math.atan2(self.vel.cross(direction),self.vel.dot(direction))
            self.vel=self.vel.rotate_rad(max(-3.2*dt,min(3.2*dt,turn)))
        old=self.pos.copy()
        self.pos+=self.vel*dt
        for axis,extent in ((0,WIDTH),(1,HEIGHT)):
            if self.pos[axis]<self.radius or self.pos[axis]>extent-self.radius:
                self.pos[axis]=max(self.radius,min(extent-self.radius,self.pos[axis]))
                self.vel[axis]*=-1
        for wall in world.cover:
            if wall.health>0 and circle_rect(self.pos,self.radius,wall.rect):
                wall.health-=34
                if old.x<wall.rect.left or old.x>wall.rect.right: self.vel.x*=-1
                else: self.vel.y*=-1
                self.pos=old
                break
        for enemy in world.enemies:
            if enemy.health>0 and enemy.id not in self.hits and self.pos.distance_to(enemy.pos)<self.radius+enemy.radius:
                world.hit_enemy(enemy,34)
                self.hits[enemy.id]=.16
                normal=normalized(self.pos-enemy.pos)
                if self.vel.dot(normal)<0: self.vel=self.vel.reflect(normal)
                self.vel=normalized(self.vel)*min(760,speed+35)
        delta=self.pos-world.player.pos
        if delta.length()<self.radius+world.player.radius and self.vel.dot(delta)<0:
            self.vel=self.vel.reflect(normalized(delta))

    def draw(self,graphics,surface,world):
        image=graphics.render_sprite(self.weapon.sprite(world,self),25,world.pak("weapon").color)
        surface.blit(image,image.get_rect(center=self.pos))
