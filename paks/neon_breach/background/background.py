"""Neon Breach: prepared AI artwork and deterministic decorative geometry."""
import pygame
from system_panic.model import WIDTH,HEIGHT
from system_panic.pak_api import BackgroundBase
class NeonBreachBackground(BackgroundBase):
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
        accent=tuple(int(c*.12) for c in [255, 148, 91])
        for inset in range(16,110,18):
            pygame.draw.rect(surface,accent,(inset,inset,WIDTH-2*inset,HEIGHT-2*inset),1,12)
