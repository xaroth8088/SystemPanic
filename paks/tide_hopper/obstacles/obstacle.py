"""Tide Hopper: procedural layouts owned by this component."""
import random
from pygame import Rect
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase
class TideHopperObstacles(ObstaclesBase):
    def init(self): self.art=self.load_asset("obstacles_sheet.png")
    def sprite(self,world,entity=None): return self.art
    def build(self,world):
        rng=random.Random(f"{world.seed}:tide_hopper:obstacles:{world.wave}")
        # Alternating canal islands, with continuous broad crossing lanes.
        layout=[]
        for x,y in ((160,65),(420,70),(720,65),(245,335),(540,330),(810,335)):
            layout.append((x+rng.randint(-30,30),y+rng.randint(-12,12),rng.randint(45,75),rng.randint(30,48)))
        return [Cover(Rect(*rect),36,36) for rect in layout]
