"""Decorative local scenery, separate from active terrain."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT
from system_panic.pak_api import BackgroundBase


class Background(BackgroundBase):
    def init(self):
        self.art = self.load_asset("background_image.png")
        self.cache = None

    def preview(self):
        return self.art

    def draw(self, surface, world):
        surface.fill((8, 21, 17))
        for y in range(0, HEIGHT, 12):
            value = y / HEIGHT
            color = tuple(int(a + (b-a)*value) for a,b in zip((8, 21, 17),(21, 43, 28)))
            pygame.draw.rect(surface,color,(0,y,WIDTH,12))
        if self.cache is None or self.cache.get_size() != surface.get_size():
            self.cache = pygame.transform.smoothscale(self.art.surface,surface.get_size())
            self.cache.set_alpha(20)
        surface.blit(self.cache,(0,0))
        for i in range(25):
            x = (i*137+41) % WIDTH
            y = (i*73+world.time*(4+i%5)) % HEIGHT
            pygame.draw.circle(surface,(48, 76, 40),(x + math.sin(world.time*.3+i)*6,y),1)
