"""Phase Garden owns its lightning visual; the host only schedules effects."""
import math
import pygame
from system_panic.model import Vec
from system_panic.pak_api import EffectBase


class ChainArc(EffectBase):
    def __init__(self, start, end,art=None):
        self.start, self.end = Vec(start), Vec(end)
        self.art=art
        self._remaining, self.alive = .16, True

    def update(self, dt):
        self._remaining -= dt
        self.alive = self._remaining > 0

    def draw(self, graphics, surface, world):
        mid = (self.start + self.end) / 2 + Vec(0, math.sin(world.time * 60) * 14)
        pygame.draw.lines(surface, world.pak("weapon").color, False, [self.start, mid, self.end], 3)
        pygame.draw.lines(surface, (225, 255, 246), False, [self.start, mid, self.end], 1)
        if self.art is not None:
            image=graphics.render_sprite(self.art.frame(int(world.time*8)%4,columns=4),17)
            surface.blit(image,image.get_rect(center=self.end))
