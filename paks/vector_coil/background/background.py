"""Vector Coil: prepared AI artwork and deterministic decorative geometry."""
import pygame
from system_panic.model import WIDTH,HEIGHT
from system_panic.pak_api import BackgroundBase
class VectorCoilBackground(BackgroundBase):
    def init(self):
        self.art=self.load_asset("background_image.png")
        self._image=None
    def preview(self): return self.art
    def draw(self,surface,world):
        surface.fill((6, 17, 13))
        if self._image is None:
            self._image=pygame.transform.scale(self.art.surface,(WIDTH,HEIGHT))
            self._image.set_alpha(7)
        surface.blit(self._image,(0,0))
        accent=tuple(int(c*.12) for c in [185, 246, 66])
        for x in range(0,WIDTH,48): pygame.draw.line(surface,accent,(x,0),(x,HEIGHT))
        for y in range(0,HEIGHT,48): pygame.draw.line(surface,accent,(0,y),(WIDTH,y))
