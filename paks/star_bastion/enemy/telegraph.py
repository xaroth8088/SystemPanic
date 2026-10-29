"""Formation attack lane, locked before the shot and dive."""
import pygame
from system_panic.model import Vec
from system_panic.pak_api import ProjectileBase

class DiveCue(ProjectileBase):
    def __init__(self,enemy):
        super().__init__(enemy.pos,Vec(),0)
        self.enemy=enemy
    def update(self,world,dt):
        self.pos=self.enemy.pos.copy()
        self.alive=self.enemy in world.enemies and self.enemy.health>0 and self.enemy.state=='lock'
    def draw(self,graphics,surface,world):
        e=self.enemy
        if e.state=='lock':
            for i in range(0,16,2):pygame.draw.line(surface,(180,80,80),e.pos+(e.target-e.pos)*i/16,e.pos+(e.target-e.pos)*(i+1)/16,2)
            pygame.draw.circle(surface,(255,155,100),e.target,16,2)
