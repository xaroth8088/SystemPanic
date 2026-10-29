"""Burrow Patrol: procedural layouts owned by this component."""
import random
from pygame import Rect
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase
class BurrowPatrolObstacles(ObstaclesBase):
    def init(self): self.art=self.load_asset("obstacles_sheet.png")
    def sprite(self,world,entity=None): return self.art.frame(int((world.time if world else 0)*8)%4,columns=4)
    def build(self,world):
        rng=random.Random(f"{world.seed}:burrow_patrol:obstacles:{world.wave}")
        # Rock veins consist of separate clusters rather than sealed walls.
        layout=[]
        for x,y in ((120,100),(350,115),(650,100),(180,315),(450,320),(760,310)):
            layout.append((x+rng.randint(-25,25),y+rng.randint(-20,20),rng.randint(42,78),rng.randint(35,60)))
        return [Cover(Rect(*rect),36,36) for rect in layout]
