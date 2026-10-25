"""Star Bastion: prepared AI artwork and deterministic decorative geometry."""
import pygame
from system_panic.model import WIDTH,HEIGHT
from system_panic.pak_api import BackgroundBase
class StarBastionBackground(BackgroundBase):
    def init(self):
        self.art=self.load_asset("background_image.png")
        self._image=None
    def preview(self): return self.art
    def draw(self,surface,world):
        surface.fill((7,15,23))
        if self._image is None:
            self._image=pygame.transform.scale(self.art.surface,(WIDTH,HEIGHT))
            self._image.set_alpha(15)
        surface.blit(self._image,(0,0))
        accent=tuple(int(c*.12) for c in [126, 189, 255])
        for i in range(100):
            x,y=(i*173+41)%WIDTH,(i*i*31+19)%HEIGHT
            pygame.draw.circle(surface,accent,(x,y),1 if i%5 else 2)
