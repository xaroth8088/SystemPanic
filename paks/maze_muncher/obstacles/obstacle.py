"""Maze Muncher: procedural layouts owned by this component."""
import random
from pygame import Rect
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase
class MazeMuncherObstacles(ObstaclesBase):
    def init(self): self.art=self.load_asset("obstacles_sheet.png")
    def sprite(self,world,entity=None): return self.art
    def take_damage(self,world,obstacle,damage):
        return 0.  # These walls are geometry, not destructible targets.

    def build(self,world):
        rng=random.Random(f"{world.seed}:maze_muncher:obstacles:{world.wave}")
        # Isolated maze elbows, with corridors at least 64 pixels across.
        layout=[]
        for x,y in ((155,90),(385,295),(650,85),(750,300)):
            x+=rng.randint(-20,20);y+=rng.randint(-15,15)
            width=rng.randint(85,125)
            layout.append((x,y,width,22))
            layout.append((x,y+22,22,rng.randint(55,80)))
        return [Cover(Rect(*rect),36,36) for rect in layout]
