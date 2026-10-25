"""Neon Breach: procedural layouts owned by this component."""
import random
from pygame import Rect
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase
class NeonBreachObstacles(ObstaclesBase):
    def init(self): self.art=self.load_asset("obstacles_sheet.png")
    def sprite(self,world,entity=None): return self.art
    def build(self,world):
        rng=random.Random(f"{world.seed}:neon_breach:obstacles:{world.wave}")
        # Destructible brick banks leave the entire perimeter open.
        sites=[(x,y) for x in (170,330,490,650,810) for y in (90,165,305)]
        layout=[(x+rng.randint(-20,20),y+rng.randint(-12,12),rng.randint(65,95),22)
                for x,y in rng.sample(sites,5+min(4,(world.wave-1)//5))]
        return [Cover(Rect(*rect),36,36) for rect in layout]
