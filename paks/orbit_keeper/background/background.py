"""OrbitKeeper: local read-only scenery; no collision or combat policy."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT
from system_panic.pak_api import BackgroundBase


class OrbitKeeperBackground(BackgroundBase):
    def init(self):
        self.art=self.load_asset('background_image.png')
        self._backdrop=None

    def preview(self):
        return self.art

    def draw(self,surface,world):
        surface.fill((13, 13, 23))
        if self._backdrop is None or self._backdrop.get_size()!=surface.get_size():
            self._backdrop=pygame.transform.smoothscale(self.art.surface,surface.get_size())
            self._backdrop.set_alpha(8)
        surface.blit(self._backdrop,(0,0))
        center=(WIDTH//2,HEIGHT//2)
        for radius in (70,115,160,205):
            pygame.draw.circle(surface,(43,39,37),center,radius,1)
        for index in range(48):
            angle=index*math.tau/48
            start=pygame.Vector2(center)+pygame.Vector2(math.cos(angle),math.sin(angle))*220
            end=pygame.Vector2(center)+pygame.Vector2(math.cos(angle),math.sin(angle))*(227 if index%4 else 232)
            pygame.draw.line(surface,(61,53,34),start,end,1)
        for index in range(70):
            x,y=(index*137+17)%WIDTH,(index*79+13)%HEIGHT
            pygame.draw.circle(surface,(31+index%20,29+index%20,37+index%25),(x,y),1)
