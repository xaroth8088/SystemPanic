"""Closed racetrack lanes: solid rails for bodies, transparent to projectiles."""
import math
import random
import pygame
from system_panic.model import Cover, Vec, normalized
from system_panic.pak_api import ObstaclesBase


def closest(p,a,b):
    edge=b-a
    return a+edge*max(0.,min(1.,(p-a).dot(edge)/max(.0001,edge.length_squared())))


class TrackRail(Cover):
    def __init__(self,a,b,color,art=None):
        self.a,self.b,self.color=a,b,color
        self.art,self._tiles=art,{}
        left,top=math.floor(min(a.x,b.x)-5),math.floor(min(a.y,b.y)-5)
        super().__init__(pygame.Rect(left,top,math.ceil(max(a.x,b.x)+5)-left+1,math.ceil(max(a.y,b.y)+5)-top+1),36,36)

    def overlaps_circle(self,p,radius):
        return self.rect.inflate(radius*2,radius*2).collidepoint(p) and closest(p,self.a,self.b).distance_squared_to(p)<(radius+4)**2

    def blocks_projectile(self,projectile):return False
    def damage(self,world,amount):return 0.
    def draw(self,graphics,surface,world):
        pygame.draw.line(surface,self.color,self.a,self.b,6)
        if self.art is not None:
            index=int(world.time*8)%4
            if index not in self._tiles:
                frame=self.art.frame(index,columns=4)
                pixels=self.art.surface.subsurface(frame.rect)
                bounds=pixels.get_bounding_rect(min_alpha=110)
                tile=pygame.transform.smoothscale(pixels.subsurface(bounds),(max(1,round(self.a.distance_to(self.b))),6))
                angle=-math.degrees(math.atan2(self.b.y-self.a.y,self.b.x-self.a.x))
                self._tiles[index]=pygame.transform.rotate(tile,angle)
            image=self._tiles[index]
            surface.blit(image,image.get_rect(center=(self.a+self.b)/2))
        pygame.draw.line(surface,(220,225,230),self.a,self.b,1)


class IronCircuitObstacles(ObstaclesBase):
    def init(self):
        self.blocks=self.load_asset("obstacles_sheet.png")
        self.points=[]
        self.width=80

    def sprite(self,world,entity=None):return self.blocks.frame(int((world.time if world else 0)*8)%4,columns=4)
    def take_damage(self,world,obstacle,damage):return 0.

    def build(self,world):
        rng=random.Random(f"{world.seed}:iron_circuit:track:{world.wave}")
        oval=[(480+340*math.cos(i*math.tau/20),240+140*math.sin(i*math.tau/20)) for i in range(20)]
        templates=(oval,
          ((200,100),(420,90),(540,150),(740,90),(820,180),(780,340),(600,390),(500,300),(350,380),(170,340),(120,220)),
          ((170,100),(790,100),(850,170),(680,230),(820,320),(760,390),(170,390),(110,320),(280,250),(110,170)),
          ((180,90),(520,90),(580,180),(780,180),(820,300),(730,390),(420,390),(360,300),(180,300),(120,200)))
        template=templates[(world.seed+world.wave)%len(templates)]
        self.points=[Vec(x+rng.randint(-4,4),y+rng.randint(-4,4)) for x,y in template]
        self.width=rng.randint(72,84)
        rails=[]
        for side in (-1,1):
            border=[]
            for i,p in enumerate(self.points):
                incoming=normalized(p-self.points[i-1])
                outgoing=normalized(self.points[(i+1)%len(self.points)]-p)
                n1,n2=Vec(-incoming.y,incoming.x),Vec(-outgoing.y,outgoing.x)
                normal=normalized(n1+n2,n2)
                distance=min(self.width, self.width/2/max(.5,abs(normal.dot(n2))))
                border.append(p+normal*distance*side)
            for i,a in enumerate(border):
                rails.append(TrackRail(a,border[(i+1)%len(border)],(230,95,86) if i%2 else (90,180,210),self.blocks))
        return rails

    def settle(self,world):
        if not self.points:return
        p=world.player
        options=[(closest(p.pos,a,b),normalized(b-a)) for a,b in zip(self.points,self.points[1:]+self.points[:1])]
        target,tangent=min(options,key=lambda item:item[0].distance_squared_to(p.pos))
        if p.pos.distance_to(target)>self.width/2-p.radius-6:
            p.pos=target.copy()
            p.angle=math.atan2(tangent.y,tangent.x)

    def on_level_start(self,world):self.settle(world)
    def on_shuffle(self,world,changed):
        if "obstacles" in changed:self.settle(world)

    def draw_floor(self,graphics,surface,world):
        if not self.points:return
        pygame.draw.lines(surface,(34,40,46),True,self.points,self.width+4)
        for point in self.points:pygame.draw.circle(surface,(34,40,46),point,self.width//2)
        for a,b in zip(self.points,self.points[1:]+self.points[:1]):
            length=a.distance_to(b)
            for distance in range(0,int(length),32):
                pygame.draw.line(surface,(160,164,125),a+(b-a)*(distance/length),a+(b-a)*(min(length,distance+13)/length),2)
