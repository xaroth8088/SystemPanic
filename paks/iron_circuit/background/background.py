"""IronCircuit: local read-only scenery; no collision or combat policy."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT
from system_panic.pak_api import BackgroundBase


class IronCircuitBackground(BackgroundBase):
    def init(self):
        self.art=self.load_asset('background_image.png')
        self._backdrop=None

    def preview(self):
        return self.art

    def draw(self,surface,world):
        surface.fill((18, 15, 14))
        if self._backdrop is None or self._backdrop.get_size()!=surface.get_size():
            self._backdrop=pygame.transform.smoothscale(self.art.surface,surface.get_size())
            self._backdrop.set_alpha(8)
        surface.blit(self._backdrop,(0,0))
        for x in range(0,WIDTH,80):
            pygame.draw.line(surface,(32,29,25),(x,0),(x,HEIGHT))
        for y in range(0,HEIGHT,80):
            pygame.draw.line(surface,(32,29,25),(0,y),(WIDTH,y))
        for index in range(20):
            y=(index*32+world.time*35)%HEIGHT
            for x in (13,WIDTH-13):
                pygame.draw.line(surface,(78,55,31),(x-5,y-5),(x+5,y+5),2)
