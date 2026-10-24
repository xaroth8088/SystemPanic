"""Iron Circuit: scenery; collision geometry lives in obstacles/."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import BackgroundBase


class IronCircuitBackground(BackgroundBase):
    def init(self):
        self.art = self.load_asset("background_image.png")
        self._backdrop = None

    def preview(self):
        return self.art

    def draw(self, surface, world):
        surface.fill((8, 16, 25))
        if self._backdrop is None or self._backdrop.get_size() != surface.get_size():
            self._backdrop = pygame.transform.scale(self.art.surface, surface.get_size())
            self._backdrop.set_alpha(16)
        surface.blit(self._backdrop, (0, 0))
        for x in range(0, WIDTH, 40):
            pygame.draw.line(surface, (15, 28, 40), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 40):
            pygame.draw.line(surface, (15, 28, 40), (0, y), (WIDTH, y))
        pygame.draw.rect(surface, (54, 42, 31), (75, 55, 810, 370), 2, border_radius=80)
        pygame.draw.rect(surface, (54, 42, 31), (120, 100, 720, 280), 1, border_radius=60)
