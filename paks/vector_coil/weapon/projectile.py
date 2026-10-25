"""Prism cross presentation; no gameplay is advanced in effect drawing."""
import pygame
from system_panic.model import Vec
from system_panic.pak_api import EffectBase

class PrismCross(EffectBase):
    def __init__(self,weapon):
        self.weapon=weapon
        self.start=Vec()
        self.ends=[]
        self.remaining=.05
        self.alive=True
    def update(self,dt):
        self.remaining-=dt
        self.alive=self.remaining>0
    def draw(self,graphics,surface,world):
        color=world.pak("weapon").color
        for end in self.ends:
            pygame.draw.line(surface,tuple(int(c*.35) for c in color),self.start,end,5)
            pygame.draw.line(surface,color,self.start,end,1)
        image=graphics.render_sprite(self.weapon.sprite(world),26,color)
        surface.blit(image,image.get_rect(center=self.start))
