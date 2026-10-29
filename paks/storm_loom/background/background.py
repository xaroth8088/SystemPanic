"""Layered indigo storm cloth, with presentation-only drifting stitchwork."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT
from system_panic.pak_api import BackgroundBase


class StormCloth(BackgroundBase):
    def init(self):
        self.art = self.load_asset('background_image.png')
        self.texture = None

    def draw(self, surface, world):
        surface.fill((11, 20, 38))
        if self.texture is None:
            self.texture = pygame.transform.smoothscale(self.art.surface, (WIDTH, HEIGHT))
            self.texture.set_alpha(9)
        surface.blit(self.texture, (0, 0))
        for lane in range(-2, 12):
            y = lane*52
            points = [(x, y+math.sin(x*.008+world.time*.25+lane*.3)*13) for x in range(0, WIDTH+1, 24)]
            pygame.draw.lines(surface, (23, 43, 62), False, points, 1)
        for i in range(40):
            x = (i*173+world.time*(7+i%4))%WIDTH
            y = (i*97)%HEIGHT
            pygame.draw.line(surface, (38, 66, 83), (x,y), (x+3,y+1), 1)
