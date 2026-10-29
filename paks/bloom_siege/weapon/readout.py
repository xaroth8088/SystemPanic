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
        # A small can travels with the pilot so the finite resource is readable
        # while watching plants, as well as in the numeric HUD.
        can=pygame.Rect(round(center.x+18),round(center.y+12),14,15)
        pygame.draw.rect(surface,(25,55,50),can,border_radius=3)
        fill=round(11*w.water/w.capacity(world))
        if fill:pygame.draw.rect(surface,(100,210,185),(can.x+2,can.bottom-2-fill,10,fill))
        pygame.draw.rect(surface,(135,210,185),can,1,border_radius=3)
        pygame.draw.arc(surface,(135,210,185),can.move(8,-3),-math.pi/2,math.pi/2,1)
        pygame.draw.line(surface,(135,210,185),can.topleft,(can.x-5,can.y-4),2)
