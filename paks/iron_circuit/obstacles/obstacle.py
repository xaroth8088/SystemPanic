"""Iron Circuit: obstacles behavior and local assets."""
import random
import pygame
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase


class IronCircuitObstacles(ObstaclesBase):

    def init(self):
        self.blocks = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.blocks

    def build(self, world):
        # A local RNG makes the level reproducible without consuming combat randomness.
        rng = random.Random(f"{world.seed}:iron_circuit:obstacles:{world.wave}")
        # Paired circuit banks create banking shots and wide driving lanes.
        layout = []
        for x in (230, 615):
            for y in (120, 310):
                layout.append((x + rng.randint(-30, 25), y + rng.randint(-22, 20),
                               rng.randint(80, 125), rng.randint(28, 44)))
        layout.append((rng.randint(440, 480), rng.randint(195, 240),
                       rng.randint(30, 50), rng.randint(30, 50)))
        health = 36
        return [Cover(pygame.Rect(*rect), health=health, max_health=health) for rect in layout]
