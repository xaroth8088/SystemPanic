"""void_drifter: a local collectible with its own motion and pickup policy."""
import math
import pygame
from system_panic.model import Vec,WIDTH,HEIGHT,normalized
from system_panic.pak_api import PowerupBase


class VoidDrifterPowerup(PowerupBase):
    def __init__(self,position,art,color,chime=None):
        super().__init__(position,10)
        self.chime = chime
        self.art,self.color=art,color
        self.age=0.
        self.vel=Vec(28,-18).rotate((position.x+position.y)%360)

    def update(self,world,dt):
        if not self.alive:return
        self.age+=dt
        if self.age>50:
            self.alive=False
            return
        self.pos+=self.vel*dt
        self.pos.x%=WIDTH
        self.pos.y%=HEIGHT
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
