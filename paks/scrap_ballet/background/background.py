"""Scenery is presentation-only: no simulation writes or RNG draws."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT, Vec
from system_panic.pak_api import BackgroundBase


class Background(BackgroundBase):
    def draw(self, surface, world):
        surface.fill((19,24,32))
        for y in range(0,HEIGHT,60):
            for x in range(0,WIDTH,80):
                pygame.draw.rect(surface,(31,37,45),(x+3,y+3,74,54),1)
                pygame.draw.circle(surface,(64,62,58),(x+9,y+9),2)
        for i in range(28):
            x=(i*193+world.time*4)%WIDTH;y=(i*97)%HEIGHT
            pygame.draw.circle(surface,(100,93,79),(x,y),1)
        pygame.draw.line(surface,(110,85,55),(0,HEIGHT-12),(WIDTH,HEIGHT-12),3)
