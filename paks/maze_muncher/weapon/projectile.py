"""Read-only dash/contact presentation; this weapon launches no waves."""
import pygame
from system_panic.pak_api import EffectBase


class BiteFlash(EffectBase):
    def __init__(self, start, end, color):
        self.start, self.end, self.color = start.copy(), end.copy(), color
        self.remaining, self.alive = .14, True

    def update(self, dt):
        self.remaining -= dt
        self.alive = self.remaining > 0

    def draw(self, graphics, surface, world):
        pygame.draw.line(surface, self.color, self.start, self.end, 3)
        pygame.draw.circle(surface, self.color, self.end, 9, 2)
