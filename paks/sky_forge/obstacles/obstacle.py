"""Sky Forge: obstacles behavior and local assets."""
import pygame
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase


class SkyForgeObstacles(ObstaclesBase):

    def init(self):
        self.blocks = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.blocks

    def build(self):
        layout = [(100, 365, 180, 18), (360, 290, 180, 18), (640, 365, 190, 18), (150, 185, 180, 18), (620, 185, 180, 18)]
        return [Cover(pygame.Rect(*rect), health=36, max_health=36) for rect in layout]

    def draw(self, graphics, surface, world, obstacle):
        accent = world.pak("obstacles").color
        pygame.draw.rect(surface, (16, 28, 39), obstacle.rect, border_radius=4)
        pygame.draw.rect(surface, tuple(int(c * .24) for c in accent), obstacle.rect, 2, border_radius=4)
        pygame.draw.line(surface, accent, obstacle.rect.topleft, obstacle.rect.topright, 2)
