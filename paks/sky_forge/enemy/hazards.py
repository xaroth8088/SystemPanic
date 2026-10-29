"""Active forge heat pressures a rooftop camper without editing movement."""
import pygame
from system_panic.model import Vec
from system_panic.pak_api import ProjectileBase

class EmberRing(ProjectileBase):
    def __init__(self,position,damage):
        super().__init__(position,Vec(),30)
        self.age,self.damage,self.hit=0.,damage,False
    def update(self,world,dt):
        self.age+=dt
        if self.age>=.85 and not self.hit and self.pos.distance_to(world.player.pos)<self.radius+world.player.radius:
            world.hit_player(self.damage)
            self.hit=True
        if self.age>1.15:self.alive=False
    def is_threat_to(self,world,body):return body is world.player
    def draw(self,graphics,surface,world):
        if self.age<.85:return
        color=(255,145,90)
        pygame.draw.circle(surface,color,self.pos,self.radius,3)
        pygame.draw.line(surface,color,self.pos-Vec(10,0),self.pos+Vec(10,0),2)
        pygame.draw.line(surface,color,self.pos-Vec(0,10),self.pos+Vec(0,10),2)
