"""Vector Coil: procedural layouts owned by this component."""
import random
from pygame import Rect
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase
class VectorCoilObstacles(ObstaclesBase):
    def init(self): self.art=self.load_asset("obstacles_sheet.png")
    def sprite(self,world,entity=None): return self.art
    def take_damage(self,world,obstacle,damage):
        return 0.  # These walls are geometry, not destructible targets.

    def build(self,world):
        rng=random.Random(f"{world.seed}:vector_coil:obstacles:{world.wave}")
        # Capacitor posts and interrupted rails invite right-angle trail circuits.
        layout=[]
        for x,y in ((160,110),(380,320),(620,110),(800,310)):
            x+=rng.randint(-25,25);y+=rng.randint(-20,20)
            layout.append((x,y,28,rng.randint(40,70)))
        layout.append((rng.randint(430,480),rng.randint(180,220),rng.randint(70,110),18))
        return [Cover(Rect(*rect),36,36) for rect in layout]
