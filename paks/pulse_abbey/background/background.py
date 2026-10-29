"""Scenery is presentation-only: no simulation writes or RNG draws."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT, Vec
from system_panic.pak_api import BackgroundBase


class Background(BackgroundBase):
    def draw(self, surface, world):
        surface.fill((20,13,32))
        for x in range(45,WIDTH,100):
            pygame.draw.line(surface,(40,28,52),(x,0),(x,HEIGHT),2)
            pygame.draw.arc(surface,(70,48,85),(x-35,20,70,100),0,math.pi,2)
            pygame.draw.arc(surface,(70,48,85),(x-35,HEIGHT-120,70,100),math.pi,math.tau,2)
        for y in range(40,HEIGHT,40):pygame.draw.line(surface,(30,23,44),(20,y),(WIDTH-20,y))
        pygame.draw.rect(surface,(95,70,110),(10,10,WIDTH-20,HEIGHT-20),2)
