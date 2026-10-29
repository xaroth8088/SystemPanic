"""Independent erodible bunker cells; all durability remains in this Pak."""
import random
import pygame
from pygame import Rect
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase

class BunkerCell(Cover):
    def draw(self,graphics,surface,world):
        color=(90,155,155) if self.health>self.max_health*.55 else (90,100,115)
        pygame.draw.rect(surface,color,self.rect)
        pygame.draw.line(surface,(150,205,195),self.rect.topleft,self.rect.topright,2)
        pygame.draw.line(surface,(35,65,80),self.rect.bottomleft,self.rect.bottomright,2)
        if self.health<self.max_health:
            pygame.draw.line(surface,(25,40,55),self.rect.topleft,self.rect.bottomright,2)

class StarBastionObstacles(ObstaclesBase):
    def init(self):self.art=self.load_asset('obstacles_sheet.png')
    def sprite(self,world,entity=None):return self.art.frame(int((world.time if world else 0)*8)%4,columns=4)
    def build(self,world):
        rng=random.Random(f'{world.seed}:star_bastion:obstacles:{world.wave}')
        cells=[]
        for base in (140,420,710):
            x=base+rng.randrange(-16,17,8);y=rng.randrange(312,337,8)
            width=rng.choice((7,8,9))
            for row in range(4):
                for column in range(width):
                    if row>=2 and 2<=column<width-2:continue
                    if row==0 and column in (0,width-1):continue
                    cells.append(BunkerCell(Rect(x+column*16,y+row*16,16,16),18,18))
        return cells
