"""Scenery is presentation-only: no simulation writes or RNG draws."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT, Vec
from system_panic.pak_api import BackgroundBase


class Background(BackgroundBase):
    def draw(self, surface, world):
        surface.fill((18,32,27))
        for i in range(90):
            x=(i*113)%WIDTH;y=(i*73)%HEIGHT
            pygame.draw.circle(surface,(29,51,36),(x,y),7+i%6,1)
        for i in range(22):
            x=(i*227+math.sin(world.time*.4+i)*8)%WIDTH;y=(i*59)%HEIGHT
            pygame.draw.circle(surface,(90,120,65),(x,y),1)
        pygame.draw.rect(surface,(50,78,53),(8,8,WIDTH-16,HEIGHT-16),2)
