"""Sky Forge: obstacles behavior and local assets."""
import random
import pygame
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase


class SkyForgeObstacles(ObstaclesBase):

    def init(self):
        self.blocks = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.blocks

    def build(self, world):
        # A local RNG makes the level reproducible without consuming combat randomness.
        rng = random.Random(f"{world.seed}:sky_forge:obstacles:{world.wave}")
        # Reachable staggered decks; bounded jitter preserves double-jump routes.
        layout = []
        for x, y in ((100, 365), (370, 285), (660, 365), (150, 185), (630, 185)):
            layout.append((x + rng.randint(-18, 18), y + rng.randint(-12, 12),
                           rng.randint(160, 200), rng.randint(14, 20)))
        if world.wave >= 7:
            layout.append((rng.randint(390, 430), rng.randint(85, 105), rng.randint(120, 160), 16))
        health = 36
        return [Cover(pygame.Rect(*rect), health=health, max_health=health) for rect in layout]

    def draw(self, graphics, surface, world, obstacle):
        accent = world.pak("obstacles").color
        pygame.draw.rect(surface, (16, 28, 39), obstacle.rect, border_radius=4)
        pygame.draw.rect(surface, tuple(int(c * .24) for c in accent), obstacle.rect, 2, border_radius=4)
        pygame.draw.line(surface, accent, obstacle.rect.topleft, obstacle.rect.topright, 2)
