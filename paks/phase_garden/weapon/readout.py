"""Positioning hint; the finite attack reach is discovered during play."""
from system_panic.model import Vec
from system_panic.pak_api import ProjectileBase

class Readout(ProjectileBase):
    def __init__(self,weapon):
        super().__init__(Vec(),Vec(),0)
        self.weapon=weapon
    def update(self,world,dt):self.pos=world.player.pos.copy()
    def draw(self,graphics,surface,world):
        pass
