"""Only the destination of an imminent creature teleport is marked."""
import pygame
from system_panic.model import Vec
from system_panic.pak_api import ProjectileBase

class RuneCue(ProjectileBase):
    def __init__(self,enemy):
        super().__init__(enemy.pos,Vec(),0)
        self.enemy=enemy
    def update(self,world,dt):
        self.pos=(self.enemy.destination if self.enemy.state=='mark' else self.enemy.pos).copy()
        if self.enemy.health<=0 or self.enemy not in world.enemies or self.enemy.state=='drift':self.alive=False
    def draw(self,graphics,surface,world):
        e=self.enemy
        if e.state=='mark':
            pygame.draw.circle(surface,(180,115,215),e.destination,e.radius+9,2)
