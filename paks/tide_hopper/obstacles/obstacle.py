"""Seeded canal islands and timber quays on the hop lattice."""
import random
import pygame
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase

class Island(Cover):
    def __init__(self,rect,kind):
        super().__init__(rect,90,90)
        self.kind=kind
    def draw(self,graphics,surface,world):
        r=self.rect
        pygame.draw.rect(surface,(6,32,35),r.move(4,5),border_radius=8)
        if self.kind=='quay':
            pygame.draw.rect(surface,(80,61,40),r,border_radius=3)
            for x in range(r.left+5,r.right,12):pygame.draw.line(surface,(139,111,64),(x,r.top+3),(x,r.bottom-3),2)
            for x in (r.left+4,r.right-5):
                for y in (r.top+4,r.bottom-5):pygame.draw.circle(surface,(192,157,88),(x,y),3)
        else:
            pygame.draw.rect(surface,(36,93,67),r,border_radius=10)
            pygame.draw.rect(surface,(85,133,82),r.inflate(-8,-8),2,border_radius=8)
            for x in range(r.left+12,r.right-4,23):
                pygame.draw.line(surface,(135,167,87),(x,r.top+10),(x+3,r.top-5),2)
                pygame.draw.circle(surface,(230,183,92),(x+3,r.top-5),3)
        if self.health<self.max_health*.6:pygame.draw.line(surface,(16,39,34),r.topleft,r.bottomright,2)

class TideHopperObstacles(ObstaclesBase):
    def init(self):self.art=self.load_asset('obstacles_sheet.png')
    def sprite(self,world,entity=None):return self.art.frame(int((world.time if world else 0)*8)%4,columns=4)
    def build(self,world):
        rng=random.Random(f'{world.seed}:tide_hopper:canals:{world.wave}')
        cells=set()
        # Two broad crossing canals and two north/south channels stay open.
        for left in (1,5,12,16):
            for top in (0,7):
                width=rng.choice((2,3));height=rng.choice((2,3))
                cells.update((x,y) for x in range(left,left+width) for y in range(top,top+height))
        result=[]
        for row in range(10):
            columns=sorted(x for x,y in cells if y==row)
            while columns:
                start=end=columns.pop(0)
                while columns and columns[0]==end+1:end=columns.pop(0)
                result.append(Island(pygame.Rect(start*48+3,row*48+3,(end-start+1)*48-6,42),'quay' if row in (1,8) else 'island'))
        return result
