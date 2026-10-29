"""Sword ownership and throw charging feedback."""
import math
import pygame
from system_panic.model import Vec,unit
from system_panic.pak_api import ProjectileBase
from .projectile import Swing

class Readout(ProjectileBase):
    def __init__(self,weapon):super().__init__(Vec(),Vec(),0);self.weapon=weapon
    def update(self,world,dt):self.pos=world.player.pos.copy()
    def draw(self,graphics,surface,world):
        w=self.weapon;color=(255,185,125)
        if w._sword is not None and w._sword.alive:return
        if not any(isinstance(s,Swing) and s.alive and s.weapon is w for s in world.projectiles):
            image=graphics.render_sprite(w.sprite(world),28,color)
            angle=world.player.angle
            image=pygame.transform.rotate(image,-math.degrees(angle))
            surface.blit(image,image.get_rect(center=self.pos+unit(angle)*25))
