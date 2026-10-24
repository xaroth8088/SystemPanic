"""Sky Forge: obstacles behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import ObstaclesBase


class SkyForgeObstacles(ObstaclesBase):

    def init(self):
        self.blocks = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.blocks

    def build(self):
        layout = [(100, 365, 180, 18), (360, 290, 180, 18), (640, 365, 190, 18), (150, 185, 180, 18), (620, 185, 180, 18)]
        return [Cover(pygame.Rect(*rect), platform=True) for rect in layout]
