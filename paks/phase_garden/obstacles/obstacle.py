"""Phase Garden: obstacles behavior and local assets."""
import random
import pygame
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase


class PhaseGardenObstacles(ObstaclesBase):

    def init(self):
        self.blocks = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.blocks

    def build(self, world):
        # A local RNG makes the level reproducible without consuming combat randomness.
        rng = random.Random(f"{world.seed}:phase_garden:obstacles:{world.wave}")
        # Disconnected hedges form a new maze without sealed rooms or narrow gates.
        layout = []
        for x in (180, 440, 700):
            x += rng.randint(-20, 20)
            gap_y = rng.randint(205, 275)
            gap = rng.randint(110, 150)
            top, bottom = rng.randint(70, 100), rng.randint(385, 415)
            if rng.random() < .5:
                layout.append((x, top, 24, gap_y - gap // 2 - top))
                layout.append((x, gap_y + gap // 2, 24, bottom - gap_y - gap // 2))
            else:
                layout.append((x - 35, top, rng.randint(90, 125), 24))
                layout.append((x, gap_y + gap // 2, 24, bottom - gap_y - gap // 2))
        health = 36
        return [Cover(pygame.Rect(*rect), health=health, max_health=health) for rect in layout]
