"""Moonlit lock canals, flowing eddies and banks; decoration is read-only."""
import math
import pygame
from system_panic.model import WIDTH,HEIGHT
from system_panic.pak_api import BackgroundBase
class TideHopperBackground(BackgroundBase):
    def init(self):self.art=self.load_asset('background_image.png')
    def preview(self):return self.art
    def draw(self,surface,world):
        surface.fill((6,30,40))
        t=world.time
        for row,y in enumerate(range(0,HEIGHT,48)):
            pygame.draw.rect(surface,(8,43,51) if row%2 else (7,37,47),(0,y,WIDTH,47))
            pygame.draw.line(surface,(24,63,65),(0,y),(WIDTH,y))
            direction=1 if row%2 else -1
            for x in range(-80,WIDTH+80,64):
                xx=(x+direction*t*12)%(WIDTH+64)-32;yy=y+24+math.sin(x*.06+t)*3
                pygame.draw.arc(surface,(35,88,88),(xx,yy-3,24,6),0,math.pi,1)
                pygame.draw.line(surface,(18,66,75),(xx+10,yy+10),(xx+35,yy+10),1)
        for x in range(24,WIDTH,48):
            for y in range(24,HEIGHT,48):pygame.draw.circle(surface,(31,70,72),(x,y),2)
        for side in (0,HEIGHT-7):
            pygame.draw.rect(surface,(43,65,58),(0,side,WIDTH,7))
            for x in range(0,WIDTH,32):pygame.draw.line(surface,(86,105,79),(x,side),(x+12,side+6),2)
        for i in range(14):
            x=(i*137+53)%WIDTH;y=14 if i%2 else HEIGHT-14
            pygame.draw.ellipse(surface,(42,105,67),(x,y,16,8))
            pygame.draw.line(surface,(9,49,47),(x+8,y+4),(x+15,y+5))
