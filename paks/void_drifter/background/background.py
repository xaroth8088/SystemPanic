"""VoidDrifter: local read-only scenery; no collision or combat policy."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT
from system_panic.pak_api import BackgroundBase


class VoidDrifterBackground(BackgroundBase):
    def init(self):
        self.art=self.load_asset('background_image.png')
        self._backdrop=None

    def preview(self):
        return self.art

    def draw(self,surface,world):
        surface.fill((8, 7, 23))
        if self._backdrop is None or self._backdrop.get_size()!=surface.get_size():
            self._backdrop=pygame.transform.smoothscale(self.art.surface,surface.get_size())
            self._backdrop.set_alpha(8)
        surface.blit(self._backdrop,(0,0))
        for index in range(110):
            depth=index%3+1
            x=(index*137+17-world.time*depth*.7)%WIDTH
            y=(index*79+13)%HEIGHT
            light=int(25+25*(.5+.5*math.sin(world.time*.6+index)))
            pygame.draw.circle(surface,(light,light,light+20),(x,y),1)
        pygame.draw.ellipse(surface,(24,18,43),(-140,-80,560,440),1)
        pygame.draw.ellipse(surface,(20,15,35),(550,150,530,420),1)
