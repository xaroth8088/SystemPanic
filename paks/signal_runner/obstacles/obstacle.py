"""Signal Runner: obstacles behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import ObstaclesBase


class SignalRunnerObstacles(ObstaclesBase):

    def init(self):
        self.blocks = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.blocks

    def build(self):
        layout = [(180, 100, 38, 110), (180, 310, 38, 70), (440, 180, 80, 38), (740, 90, 38, 90), (740, 280, 38, 110)]
        return [Cover(pygame.Rect(*rect), platform=False) for rect in layout]
