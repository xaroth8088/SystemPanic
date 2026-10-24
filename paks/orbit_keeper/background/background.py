"""Orbit Keeper: scenery; collision geometry lives in obstacles/."""
import pygame
from system_panic.model import WIDTH, HEIGHT
from system_panic.pak_api import BackgroundBase


class OrbitKeeperBackground(BackgroundBase):
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
        for r in (90, 140, 190, 225):
            pygame.draw.circle(surface, (48, 46, 33), (WIDTH // 2, HEIGHT // 2), r, 1)
