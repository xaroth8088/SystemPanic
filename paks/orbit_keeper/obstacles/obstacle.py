"""Orbit Keeper: obstacles behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import ObstaclesBase


class OrbitKeeperObstacles(ObstaclesBase):

    def init(self):
        self.blocks = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.blocks

    def build(self):
        layout = [(440, 200, 80, 80), (130, 100, 32, 32), (798, 100, 32, 32), (130, 348, 32, 32), (798, 348, 32, 32)]
        return [Cover(pygame.Rect(*rect), platform=False) for rect in layout]
