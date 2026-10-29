"""Warm refractory tiles and slow embers, wholly separate from collisions."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT
from system_panic.pak_api import BackgroundBase


class RefractoryFloor(BackgroundBase):
    def init(self):
        self.art = self.load_asset('background_image.png')
        self.texture = None

    def draw(self, surface, world):
        surface.fill((28, 20, 25))
        if self.texture is None:
            self.texture = pygame.transform.smoothscale(self.art.surface, (WIDTH, HEIGHT))
            self.texture.set_alpha(9)
        surface.blit(self.texture, (0, 0))
        for y in range(0, HEIGHT, 48):
            offset = 32 if (y//48)%2 else 0
            for x in range(-64+offset, WIDTH, 64):
                pygame.draw.rect(surface, (43, 30, 31), (x+2,y+2,60,44), 1, border_radius=4)
        for i in range(30):
            x = (i*179+math.sin(world.time*.5+i)*8)%WIDTH
            y = (i*83-world.time*(6+i%5))%HEIGHT
            pygame.draw.circle(surface, (91+i%3*15,48,33), (x,y), 1)
