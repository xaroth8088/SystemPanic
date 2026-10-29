"""SignalRunner: local read-only scenery; no collision or combat policy."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT
from system_panic.pak_api import BackgroundBase


class SignalRunnerBackground(BackgroundBase):
    def init(self):
        self.art=self.load_asset('background_image.png')
        self._backdrop=None

    def preview(self):
        return self.art

    def draw(self,surface,world):
        surface.fill((5, 15, 25))
        if self._backdrop is None or self._backdrop.get_size()!=surface.get_size():
            self._backdrop=pygame.transform.smoothscale(self.art.surface,surface.get_size())
            self._backdrop.set_alpha(8)
        surface.blit(self._backdrop,(0,0))
        for row in range(6):
            y=36+row*78
            pygame.draw.line(surface,(13,34,48),(0,y),(WIDTH,y),1)
            for column in range(7):
                x=45+column*142
                pygame.draw.line(surface,(13,34,48),(x,y),(x,y+35),1)
                pygame.draw.circle(surface,(23,62,75),(x,y),3,1)
            pulse=(world.time*60+row*157)%WIDTH
            pygame.draw.line(surface,(28,79,100),(pulse-16,y),(pulse,y),2)
