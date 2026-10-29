"""Scenery is presentation-only: no simulation writes or RNG draws."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT, Vec
from system_panic.pak_api import BackgroundBase


class Background(BackgroundBase):
    def draw(self, surface, world):
        surface.fill((13,20,39))
        for x in range(0,WIDTH,80):
            for y in range(0,HEIGHT,80):
                pygame.draw.circle(surface,(27,40,64),(x,y),32,1)
                angle=world.time*.14+x*.01+y*.02
                end=Vec(x,y)+Vec(math.cos(angle),math.sin(angle))*23
                pygame.draw.line(surface,(38,57,86),(x,y),end,1)
        pygame.draw.rect(surface,(55,85,125),(6,6,WIDTH-12,HEIGHT-12),2)
