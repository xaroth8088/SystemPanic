"""Permanent jump-connected platform graphs with several arrangement families."""
import random
import pygame
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase


class SkyForgeObstacles(ObstaclesBase):
    def init(self):
        self.blocks = self.load_asset("obstacles_sheet.png")
        self.routes = []

    def sprite(self, world, entity=None):
        return self.blocks

    def take_damage(self, world, obstacle, damage):
        return 0.

    def build(self, world):
        rng = random.Random(f"{world.seed}:sky_forge:obstacles:{world.wave}")
        # Every step rises <= 86 px and leaves <= 90 px between landing edges.
        # A 330 px/s double jump at gravity 820 and run speed 220 reaches these.
        templates = (
            ((175,380),(355,302),(535,224),(715,146),(535,68)),
            ((175,380),(355,302),(535,224),(415,146),(235,68),(775,380)),
            ((180,380),(300,302),(180,224),(300,146),(480,68),
             (780,380),(660,302),(780,224),(660,146)),
            ((180,380),(480,380),(780,380),(300,302),(660,302),
             (180,224),(480,224),(780,224),(300,146),(660,146),(480,68)),
            ((480,380),(360,302),(600,302),(480,224),(360,146),(600,146),(480,68)),
        )
        family = (world.wave + world.seed) % len(templates)
        walls = []
        for x,y in templates[family]:
            width = rng.randint(138,166)
            walls.append(Cover(pygame.Rect(x-width/2+rng.randint(-5,5),y+rng.randint(-3,3),width,16),36,36))
        # Explicit parent links document the construction's connected jump graph.
        self.routes = []
        pending = set(range(len(walls)))
        reached = {-1}
        while pending:
            progress = False
            for target in sorted(pending):
                b = walls[target].rect
                for source in sorted(reached):
                    a = walls[source].rect if source >= 0 else pygame.Rect(0,458,960,1)
                    gap = max(0,a.left-b.right,b.left-a.right)
                    rise = a.top-b.top
                    if 0 < rise <= 90 and gap <= 90:
                        self.routes.append((source,target))
                        reached.add(target)
                        pending.remove(target)
                        progress = True
                        break
            if not progress:
                raise ValueError("Unreachable Sky Forge platform layout")
        return walls

    def draw(self, graphics, surface, world, obstacle):
        accent = world.pak("obstacles").color
        pygame.draw.rect(surface,(16,28,39),obstacle.rect,border_radius=4)
        pygame.draw.rect(surface,tuple(int(c*.3) for c in accent),obstacle.rect,2,border_radius=4)
        pygame.draw.line(surface,accent,obstacle.rect.topleft,obstacle.rect.topright,2)
