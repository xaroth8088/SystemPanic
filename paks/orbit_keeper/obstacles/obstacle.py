"""Orbit Keeper: obstacles behavior and local assets."""
import random
import math
import pygame
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase


class OrbitKeeperObstacles(ObstaclesBase):

    def take_damage(self,world,obstacle,damage):return 0.

    def init(self):
        self.blocks = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.blocks.frame(int((world.time if world else 0)*8)%4,columns=4)

    def build(self, world):
        # A local RNG makes the level reproducible without consuming combat randomness.
        rng = random.Random(f"{world.seed}:orbit_keeper:obstacles:{world.wave}")
        # Rotating elliptical satellite fields leave the center orbit mostly open.
        size = rng.randint(60, 82)
        layout = [(480 - size // 2 + rng.randint(-8, 8), 240 - size // 2 + rng.randint(-8, 8), size, size)]
        phase = rng.uniform(0, math.tau)
        count = 4 if world.wave < 10 else 6
        for i in range(count):
            angle = phase + i * math.tau / count
            x = 480 + math.cos(angle) * rng.randint(300, 355)
            y = 240 + math.sin(angle) * rng.randint(145, 170)
            size = rng.randint(24, 38)
            layout.append((int(x - size / 2), int(y - size / 2), size, size))
        health = 36
        return [Cover(pygame.Rect(*rect), health=health, max_health=health) for rect in layout]
