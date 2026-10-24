"""Iron Circuit: obstacles behavior and local assets."""
import pygame
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase


class IronCircuitObstacles(ObstaclesBase):

    def init(self):
        self.blocks = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.blocks

    def build(self):
        layout = [(240, 130, 110, 42), (240, 308, 110, 42), (610, 130, 110, 42), (610, 308, 110, 42), (456, 216, 48, 48)]
        return [Cover(pygame.Rect(*rect), health=36, max_health=36) for rect in layout]
