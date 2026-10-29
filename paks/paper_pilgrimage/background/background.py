"""Quiet layered paper scenery. No gameplay state or RNG is touched."""
import pygame
from system_panic.pak_api import BackgroundBase


class PaperBackground(BackgroundBase):
    def init(self):
        self.art = self.load_asset('background_image.png')
        self.texture = None

    def draw(self, surface, world):
        surface.fill((18, 25, 38))
        if self.texture is None:
            self.texture = pygame.transform.smoothscale(self.art.surface, (960, 480))
            self.texture = self.texture.copy()
            self.texture.set_alpha(10)
        surface.blit(self.texture, (0, 0))
        for x in range(-480, 960, 160):
            pygame.draw.lines(surface, (30, 43, 60), False, [(x, 480), (x+240, 0), (x+480, 480)], 1)
        pygame.draw.rect(surface, (64, 83, 107), (4, 4, 952, 472), 2)
