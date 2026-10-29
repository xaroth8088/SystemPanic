"""PhaseGarden: local read-only scenery; no collision or combat policy."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT
from system_panic.pak_api import BackgroundBase


class PhaseGardenBackground(BackgroundBase):
    def init(self):
        self.art=self.load_asset('background_image.png')
        self._backdrop=None

    def preview(self):
        return self.art

    def draw(self,surface,world):
        surface.fill((6, 20, 18))
        if self._backdrop is None or self._backdrop.get_size()!=surface.get_size():
            self._backdrop=pygame.transform.smoothscale(self.art.surface,surface.get_size())
            self._backdrop.set_alpha(8)
        surface.blit(self._backdrop,(0,0))
        for index in range(38):
            x=(index*191+30)%WIDTH
            y=(index*97+30)%HEIGHT
            radius=5+int(2*math.sin(world.time*.7+index))
            pygame.draw.circle(surface,(17,43,34),(x,y),radius,1)
            pygame.draw.line(surface,(17,43,34),(x,y+radius),(x+4,y+radius+13),1)
        for index in range(14):
            x=(index*251+world.time*5)%WIDTH
            y=(index*113+math.sin(world.time+index)*9)%HEIGHT
            pygame.draw.circle(surface,(42,77,57),(x,y),1)
