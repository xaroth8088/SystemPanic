"""Burrow ripples and a locked emergence rush, with no hidden damage."""
import pygame
from system_panic.model import Vec
from system_panic.pak_api import ProjectileBase

class WormCue(ProjectileBase):
    def __init__(self,enemy):
        super().__init__(enemy.pos,Vec(),0)
        self.enemy=enemy
    def update(self,world,dt):
        self.pos=self.enemy.pos.copy()
        self.alive=self.enemy in world.enemies and self.enemy.health>0 and self.enemy.state in ('burrow','emerge')
    def draw(self,graphics,surface,world):
        e=self.enemy
        pygame.draw.circle(surface,(210,145,85),e.pos,int(18+e.timer*10),2)
        if e.state=='emerge':pygame.draw.line(surface,(255,185,120),e.pos,e.target,2)
