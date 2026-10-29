"""vector_coil: a local collectible with its own motion and pickup policy."""
import math
import pygame
from system_panic.model import Vec,WIDTH,HEIGHT,normalized
from system_panic.pak_api import PowerupBase


class VectorCoilPowerup(PowerupBase):
    def __init__(self,position,art,color,chime=None):
        super().__init__(position,10)
        self.chime = chime
        self.art,self.color=art,color
        self.age=0.
        self.vel=Vec()

    def update(self,world,dt):
        if not self.alive:return
        self.age+=dt
        if self.age>50:
            self.alive=False
            return
        delta=world.player.pos-self.pos
        if abs(delta.x)>abs(delta.y):self.vel=Vec(1 if delta.x>0 else -1,0)*95
        else:self.vel=Vec(0,1 if delta.y>0 else -1)*95
        self.pos+=self.vel*min(dt,delta.length()/95)
        if self.pos.distance_to(world.player.pos)<=self.radius+world.player.radius+3:
            if world.collect_powerup(self) and self.chime is not None:
                self.chime.play(volume=.45)

    def draw(self,graphics,surface,world):
        radius=12+int(2*math.sin(self.age*5))
        pygame.draw.circle(surface,self.color,self.pos,radius,2)
        image=graphics.render_sprite(self.art.frame(int(self.age*8)%4,columns=4),16,self.color)
        surface.blit(image,image.get_rect(center=self.pos))
        pygame.draw.line(surface,(240,245,210),self.pos+Vec(-3,-17),self.pos+Vec(3,-17),2)
        pygame.draw.line(surface,(240,245,210),self.pos+Vec(0,-20),self.pos+Vec(0,-14),2)
