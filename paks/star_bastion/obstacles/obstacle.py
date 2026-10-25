"""Star Bastion: procedural layouts owned by this component."""
import random
from pygame import Rect
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase
class StarBastionObstacles(ObstaclesBase):
    def init(self): self.art=self.load_asset("obstacles_sheet.png")
    def sprite(self,world,entity=None): return self.art
    def build(self,world):
        rng=random.Random(f"{world.seed}:star_bastion:obstacles:{world.wave}")
        # Three bunkers have broad entrances and a clear upper formation field.
        layout=[]
        for x in (150,420,710):
            x+=rng.randint(-18,18);y=rng.randint(315,345)
            width=rng.randint(115,140)
            layout.extend([(x,y,width,18),(x,y+18,22,38),(x+width-22,y+18,22,38)])
        return [Cover(Rect(*rect),36,36) for rect in layout]
