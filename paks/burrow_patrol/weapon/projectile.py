"""Visual pressure tether; the weapon owns inflation/damage in active updates."""
import pygame
from system_panic.model import Vec
from system_panic.pak_api import EffectBase

class PressureLine(EffectBase):
    def __init__(self,weapon):
        self.weapon=weapon
        self.start,self.end=Vec(),Vec()
        self.pressure=0.
        self.remaining=.05
        self.alive=True
    def update(self,dt):
        self.remaining-=dt
        self.alive=self.remaining>0
    def draw(self,graphics,surface,world):
        color=world.pak("weapon").color
        pygame.draw.line(surface,color,self.start,self.end,2)
        pygame.draw.circle(surface,color,self.end,int(18+self.pressure*18),2)
        image=graphics.render_sprite(self.weapon.sprite(world),int(20+self.pressure*20),color)
        surface.blit(image,image.get_rect(center=self.end))
