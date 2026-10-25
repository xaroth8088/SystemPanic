"""neon_breach: a local collectible with its own motion and pickup policy."""
import math
import pygame
from system_panic.model import Vec,WIDTH,HEIGHT,normalized
from system_panic.pak_api import PowerupBase


class NeonBreachPowerup(PowerupBase):
    def __init__(self,position,art,color):
        super().__init__(position,10)
        self.art,self.color=art,color
        self.age=0.
        self.vel=Vec(120,-90).rotate((position.x*.2)%360)

    def update(self,world,dt):
        if not self.alive:return
        self.age+=dt
        if self.age>50:
            self.alive=False
            return
        delta=world.player.pos-self.pos
        if delta.length()<170:self.vel=self.vel.lerp(normalized(delta)*160,min(1,dt*3))
        self.pos+=self.vel*dt
        for axis,limit in ((0,WIDTH),(1,HEIGHT)):
            if self.pos[axis]<self.radius or self.pos[axis]>limit-self.radius:
                self.vel[axis]*=-1
                self.pos[axis]=max(self.radius,min(limit-self.radius,self.pos[axis]))
        if self.pos.distance_to(world.player.pos)<=self.radius+world.player.radius+3:
            world.collect_powerup(self)

    def draw(self,graphics,surface,world):
        radius=12+int(2*math.sin(self.age*5))
        pygame.draw.circle(surface,self.color,self.pos,radius,2)
        image=graphics.render_sprite(self.art,16,self.color)
        surface.blit(image,image.get_rect(center=self.pos))
        pygame.draw.line(surface,(240,245,210),self.pos+Vec(-3,-17),self.pos+Vec(3,-17),2)
        pygame.draw.line(surface,(240,245,210),self.pos+Vec(0,-20),self.pos+Vec(0,-14),2)
