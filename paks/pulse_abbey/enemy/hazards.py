"""Only active Pak-owned hazards are drawn; delayed damage timing stays local."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT
from system_panic.pak_api import ProjectileBase




class Bolt(ProjectileBase):
    def __init__(self, position, velocity, damage, radius=4):
        super().__init__(position,velocity,radius)
        self.damage,self.age=damage,0.

    def update(self, world, dt):
        self.age+=dt
        previous=self.pos.copy()
        self.pos+=self.vel*dt
        if self.age>4 or not(-8<self.pos.x<WIDTH+8 and -8<self.pos.y<HEIGHT+8):self.alive=False
        for wall in world.geometry:
            if wall.health>0 and wall.blocks_projectile(self) and wall.overlaps_segment(previous,self.pos):
                world.hit_cover(wall,self.damage)
                self.alive=False
                return
        if self.pos.distance_to(world.player.pos)<world.player.radius+self.radius:
            world.hit_player(self.damage)
            self.alive=False

    def is_threat_to(self, world, body):
        return body is world.player

    def draw(self, graphics, surface, world):
        pygame.draw.line(surface,(125,65,95),self.pos-self.vel*.04,self.pos,3)
        pygame.draw.circle(surface,(255,140,165),self.pos,self.radius)
        pygame.draw.circle(surface,(255,235,215),self.pos,2)


class Zone(ProjectileBase):
    def __init__(self, position, radius, delay, damage, duration=.35):
        super().__init__(position,Vec(),radius)
        self.delay,self.damage,self.duration,self.age=delay,damage,duration,0.

    def update(self, world, dt):
        self.age+=dt
        if self.age>=self.delay:
            if self.pos.distance_to(world.player.pos)<self.radius+world.player.radius:
                world.hit_player(self.damage)
            if self.age>self.delay+self.duration:self.alive=False

    def is_threat_to(self, world, body):
        return body is world.player

    def draw(self, graphics, surface, world):
        if self.age<self.delay:return
        pygame.draw.circle(surface,(255,115,160),self.pos,int(self.radius),3)
        pygame.draw.line(surface,(255,150,190),self.pos-Vec(8,8),self.pos+Vec(8,8),2)
        pygame.draw.line(surface,(255,150,190),self.pos-Vec(-8,8),self.pos+Vec(-8,8),2)
