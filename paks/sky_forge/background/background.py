"""SkyForge: local read-only scenery; no collision or combat policy."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT
from system_panic.pak_api import BackgroundBase


class SkyForgeBackground(BackgroundBase):
    def init(self):
        self.art=self.load_asset('background_image.png')
        self._backdrop=None

    def preview(self):
        return self.art

    def draw(self,surface,world):
        surface.fill((18, 11, 20))
        for y in range(0,HEIGHT,12):
            pygame.draw.rect(surface,(18+int(y*.045),11+int(y*.012),20-int(y*.008)),(0,y,WIDTH,12))
        if self._backdrop is None or self._backdrop.get_size()!=surface.get_size():
            self._backdrop=pygame.transform.smoothscale(self.art.surface,surface.get_size())
            self._backdrop.set_alpha(8)
        surface.blit(self._backdrop,(0,0))
        for index in range(18):
            x=(index*173+31)%WIDTH
            y=HEIGHT-(index*89+world.time*(9+index%7))%HEIGHT
            pygame.draw.circle(surface,(76,39+index%20,30),(x+math.sin(world.time*.5+index)*8,y),1)
        for index in range(8):
            x=index*150-30
            pygame.draw.rect(surface,(28,19,28),(x,0,16,145+index%3*45))
        pygame.draw.line(surface,(88,39,36),(0,HEIGHT-3),(WIDTH,HEIGHT-3),3)
