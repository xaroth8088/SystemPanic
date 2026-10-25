"""Void Drifter: obstacles behavior and local assets."""
import random
import pygame
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase


class VoidDrifterObstacles(ObstaclesBase):

    def init(self):
        self.blocks = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.blocks

    def build(self, world):
        # A local RNG makes the level reproducible without consuming combat randomness.
        rng = random.Random(f"{world.seed}:void_drifter:obstacles:{world.wave}")
        # Sparse drifting debris, with a few more islands as the field ages.
        sites = [(220, 110), (670, 325), (740, 105), (285, 340), (510, 85), (840, 235)]
        count = 2 + min(3, (world.wave - 1) // 6)
        layout = [(x + rng.randint(-40, 40), y + rng.randint(-30, 30),
                   rng.randint(26, 46), rng.randint(26, 46)) for x, y in rng.sample(sites, count)]
        health = 36
        return [Cover(pygame.Rect(*rect), health=health, max_health=health) for rect in layout]
