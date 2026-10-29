"""Read-only aiming/charge feedback scheduled with this weapon's transients."""
import math
import pygame
from system_panic.model import Vec
from system_panic.pak_api import ProjectileBase


class Readout(ProjectileBase):
    def __init__(self, weapon):
        super().__init__(Vec(), Vec(), 0)
        self.weapon = weapon

    def update(self, world, dt):
        self.pos = world.player.pos.copy()

    def draw(self, graphics, surface, world):
        w = self.weapon
        color = (255, 110, 110) if w.locked else world.pak('weapon').color
        fraction = min(1., w.heat if w.heat else w.charge / 1.2)
        center = self.pos
        if fraction > .01:
            pygame.draw.circle(surface, tuple(int(c * .45) for c in color), center, 22, 1)
            pygame.draw.arc(surface, color, pygame.Rect(center.x-23, center.y-23, 46, 46), -math.pi/2, -math.pi/2+math.tau*max(.01,fraction), 3)
        count=len(w.orbiters())
        loose=sum(s.state=='free' for s in w.active)
