"""Pool and deliberate catch timing are local to returning blades."""
import pygame
from system_panic.model import Vec
from system_panic.pak_api import ProjectileBase

class Readout(ProjectileBase):
    def __init__(self,weapon):
        super().__init__(Vec(),Vec(),0)
        self.weapon=weapon
    def update(self,world,dt):self.pos=world.player.pos.copy()
    def draw(self,graphics,surface,world):
        w=self.weapon
        incoming=any(s.alive and s.returning and s.pos.distance_to(self.pos)<90 for s in w._active)
        cue='EMPOWERED THROW' if w.next_boost>1 else 'CATCH WINDOW' if w.catch_window>0 else 'RELEASE FOR CATCH' if incoming and w._held_for>=.35 else 'HOLD TO CAST / TIME RELEASE AS BLADES RETURN'
        color=(255,230,135) if incoming or w.next_boost>1 else world.pak('weapon').color
        count=sum(s.alive and s in world.projectiles for s in w._active)
        pass
        if w.catch_flash>0:pygame.draw.circle(surface,(255,235,160),self.pos,24,3)
