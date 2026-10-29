"""A quiet induction dock; fixed texture and field lines are presentation only."""
import math
import pygame
from system_panic.pak_api import BackgroundBase


class FerricBackground(BackgroundBase):
    def init(self):
        self.art = self.load_asset('background_image.png')
        self.texture = None

    def draw(self, surface, world):
        surface.fill((17, 24, 32))
        if self.texture is None:
            self.texture = pygame.transform.smoothscale(self.art.surface, (960, 480)).copy()
            self.texture.set_alpha(20)
        surface.blit(self.texture, (0, 0))
        for y in range(28, 480, 45):
            pygame.draw.line(surface, (28, 39, 48), (12, y), (948, y), 1)
        for x in range(28, 960, 70):
            pygame.draw.line(surface, (26, 36, 45), (x, 12), (x, 468), 1)
        pygame.draw.rect(surface, (65, 88, 105), (4, 4, 952, 472), 2)
