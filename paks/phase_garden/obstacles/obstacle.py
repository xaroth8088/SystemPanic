"""Phase Garden: obstacles behavior and local assets."""
import pygame
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase


class PhaseGardenObstacles(ObstaclesBase):

    def init(self):
        self.blocks = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.blocks

    def build(self):
        layout = [(185, 100, 24, 120), (185, 300, 24, 80), (380, 100, 120, 24), (460, 300, 24, 120), (690, 100, 24, 120), (690, 300, 130, 24)]
        return [Cover(pygame.Rect(*rect), health=36, max_health=36) for rect in layout]
