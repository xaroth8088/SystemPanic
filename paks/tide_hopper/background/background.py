"""Tide Hopper: prepared AI artwork and deterministic decorative geometry."""
import pygame
from system_panic.model import WIDTH,HEIGHT
from system_panic.pak_api import BackgroundBase
class TideHopperBackground(BackgroundBase):
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
        accent=tuple(int(c*.12) for c in [66, 231, 207])
        for y in range(50,HEIGHT,60):
            pygame.draw.line(surface,accent,(0,y),(WIDTH,y),2)
            for x in range(0,WIDTH,80): pygame.draw.line(surface,accent,(x,y+24),(x+25,y+24),1)
