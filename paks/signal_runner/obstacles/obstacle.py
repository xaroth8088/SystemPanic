"""Signal Runner: obstacles behavior and local assets."""
import random
import pygame
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase


class SignalRunnerObstacles(ObstaclesBase):

    def init(self):
        self.blocks = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.blocks.frame(int((world.time if world else 0)*8)%4,columns=4)

    def take_damage(self, world, obstacle, damage):
        return 0.

    def build(self, world):
        # A local RNG makes the level reproducible without consuming combat randomness.
        rng = random.Random(f"{world.seed}:signal_runner:obstacles:{world.wave}")
        # Broken signal-room partitions; broad doors remain traversable by every pilot.
        layout = []
        for anchor in (190, 450, 740):
            x = anchor + rng.randint(-28, 28)
            gap = rng.randint(105, 145)
            door = rng.randint(180, 280)
            thickness = rng.randint(26, 40)
            top, bottom = rng.randint(65, 100), rng.randint(390, 420)
            layout.extend([(x, top, thickness, door - gap // 2 - top),
                           (x, door + gap // 2, thickness, bottom - door - gap // 2)])
        health = 36
        return [Cover(pygame.Rect(*rect), health=health, max_health=health) for rect in layout]
