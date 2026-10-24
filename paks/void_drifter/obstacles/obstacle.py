"""Void Drifter: obstacles behavior and local assets."""
import pygame
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase


class VoidDrifterObstacles(ObstaclesBase):

    def init(self):
        self.blocks = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.blocks

    def build(self):
        layout = [(275, 130, 32, 32), (660, 310, 40, 40)]
        return [Cover(pygame.Rect(*rect), health=36, max_health=36) for rect in layout]
