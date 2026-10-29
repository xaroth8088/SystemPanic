"""Scenery is presentation-only: no simulation writes or RNG draws."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT, Vec
from system_panic.pak_api import BackgroundBase


class Background(BackgroundBase):
    def draw(self, surface, world):
        surface.fill((17,29,40))
        for x in range(-HEIGHT,WIDTH,100):
            points=[(x,HEIGHT),(x+HEIGHT//2,0),(x+HEIGHT,HEIGHT)]
            pygame.draw.lines(surface,(27,49,60),False,points,1)
        for y in range(0,HEIGHT,60):pygame.draw.line(surface,(24,45,55),(0,y),(WIDTH,y))
        pygame.draw.rect(surface,(75,135,145),(4,4,WIDTH-8,HEIGHT-8),2)
