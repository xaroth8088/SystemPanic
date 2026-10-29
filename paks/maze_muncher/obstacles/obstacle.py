"""Seeded braided maze with short exits at a randomly chosen height."""
import random
import pygame
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase

class MazeMuncherObstacles(ObstaclesBase):
    def init(self):self.art=self.load_asset('obstacles_sheet.png')
    def sprite(self,world,entity=None):return self.art.frame(int((world.time if world else 0)*8)%4,columns=4)
    def take_damage(self,world,obstacle,damage):return 0.
    def build(self,world):
        rng=random.Random(f'{world.seed}:maze_muncher:maze:{world.wave}')
        walls=[[True]*30 for _ in range(15)]
        stack=[(rng.randrange(14),rng.randrange(7))];visited=set(stack)
        while stack:
            x,y=stack[-1];walls[y*2+1][x*2+1]=False
            options=[(x+dx,y+dy,dx,dy) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)) if 0<=x+dx<14 and 0<=y+dy<7 and (x+dx,y+dy) not in visited]
            if not options:stack.pop();continue
            nx,ny,dx,dy=rng.choice(options)
            walls[y*2+1+dy][x*2+1+dx]=False
            visited.add((nx,ny));stack.append((nx,ny))
        # Add alternate chase routes instead of a tree made only of dead ends.
        for y in range(1,14):
            for x in range(1,28):
                if walls[y][x] and (x+y)%2 and rng.random()<.22:walls[y][x]=False
        self._exit_row=rng.choice(tuple(range(1,14,2)))
        # Each stub joins the existing maze; no entire row is cleared.
        for x in (0,28,29):walls[self._exit_row][x]=False
        for y in range(6,9):
            for x in range(13,17):walls[y][x]=False
        merged=[];active={}
        for y,row in enumerate(walls):
            spans=[];x=0
            while x<30:
                if not row[x]:x+=1;continue
                start=x
                while x<30 and row[x]:x+=1
                spans.append((start,x-start))
            current={}
            for span in spans:
                if span in active:
                    rect=active[span];rect.height+=32
                else:
                    rect=pygame.Rect(span[0]*32,y*32,span[1]*32,32);merged.append(rect)
                current[span]=rect
            active=current
        return [Cover(rect,36,36) for rect in merged]
    def draw(self,graphics,surface,world,obstacle):
        rect=obstacle.rect
        pygame.draw.rect(surface,(10,18,55),rect)
        pygame.draw.rect(surface,(35,100,225),rect.inflate(-4,-4),2,border_radius=6)
        if rect.width>12 and rect.height>12:pygame.draw.rect(surface,(65,185,245),rect.inflate(-12,-12),1,border_radius=3)
    def draw_floor(self,graphics,surface,world):
        y=16+self._exit_row*32
        for x,direction in ((7,1),(953,-1)):
            pygame.draw.lines(surface,(95,220,255),False,[(x-direction*3,y-7),(x+direction*3,y),(x-direction*3,y+7)],2)
