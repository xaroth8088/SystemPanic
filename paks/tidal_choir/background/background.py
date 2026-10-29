"""Scenery is presentation-only: no simulation writes or RNG draws."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT, Vec
from system_panic.pak_api import BackgroundBase


class Background(BackgroundBase):
    def draw(self, surface, world):
        surface.fill((9,29,46))
        for y in range(20,HEIGHT,32):
            points=[(x,y+math.sin(x*.016+world.time*.7+y)*5) for x in range(0,WIDTH+1,16)]
            pygame.draw.lines(surface,(16,47,64),False,points,1)
        for i in range(45):
            x=(i*157)%WIDTH;y=(i*97-world.time*(8+i%4))%HEIGHT
            pygame.draw.circle(surface,(44,87,102),(x,y),1+i%3,1)
