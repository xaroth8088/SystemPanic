"""Weapon-owned polygon obstacles and enemy-only live-tail collision."""
import math
import pygame
from system_panic.model import Cover, Enemy, Vec, normalized


def closest(point,a,b):
    edge=b-a
    if not edge.length_squared():return a.copy()
    return a+edge*max(0.,min(1.,(point-a).dot(edge)/edge.length_squared()))


def inside(point,points):
    result=False
    for a,b in zip(points,points[1:]+points[:1]):
        if (a.y>point.y)!=(b.y>point.y) and point.x<a.x+(point.y-a.y)*(b.x-a.x)/(b.y-a.y):
            result=not result
    return result


def bounds(points,padding=0):
    left=math.floor(min(p.x for p in points)-padding)
    top=math.floor(min(p.y for p in points)-padding)
    return pygame.Rect(left,top,math.ceil(max(p.x for p in points)+padding)-left+1,
                       math.ceil(max(p.y for p in points)+padding)-top+1)


class CarvedArea(Cover):
    def __init__(self,points,color,inset=14):
        self.points=[p.copy() for p in points]
        self.color=color
        self.inset=inset
        super().__init__(bounds(self.points),1,1)

    def overlaps_circle(self,position,radius):
        if not self.rect.inflate(radius*2,radius*2).collidepoint(position):return False
        distance=min(closest(position,a,b).distance_to(position)
                     for a,b in zip(self.points,self.points[1:]+self.points[:1]))
        # Reserve the drawn boundary as a walkable lane, including edge-to-edge
        # captures. Otherwise a large loop can entomb its own pilot at closure.
        return distance+radius>self.inset if inside(position,self.points) else radius>distance+self.inset

    def overlaps_segment(self,start,end):
        steps=max(1,math.ceil(start.distance_to(end)/4))
        return any(self.overlaps_circle(start.lerp(end,i/steps),0) for i in range(steps+1))

    def damage(self,world,amount):return 0.

    def draw(self,graphics,surface,world):
        layer=pygame.Surface(surface.get_size(),pygame.SRCALPHA)
        pygame.draw.polygon(layer,(*self.color,55),self.points)
        pygame.draw.lines(layer,(0,0,0,0),True,self.points,int(self.inset*2))
        for point in self.points:pygame.draw.circle(layer,(0,0,0,0),point,int(self.inset))
        surface.blit(layer,(0,0))
        pygame.draw.lines(surface,self.color,True,self.points,2)


class LiveLine(Cover):
    def __init__(self,a,b,weapon,width):
        self.a,self.b,self.weapon,self.width=a.copy(),b.copy(),weapon,width
        super().__init__(bounds([a,b],width),1,1)

    def blocks_body(self,body):return isinstance(body,Enemy)
    def blocks_projectile(self,projectile):return False

    def overlaps_circle(self,position,radius):
        if not self.rect.inflate(radius*2,radius*2).collidepoint(position):return False
        return closest(position,self.a,self.b).distance_squared_to(position)<(radius+self.width)**2

    def on_contact(self,world,body,normal):
        away=normalized(body.pos-closest(body.pos,self.a,self.b),normal)
        body.vel-=away*(2*body.vel.dot(away))
        body.pos+=away*6
        count=world.powerups_collected
        if count and world.time>=self.weapon._line_hits.get(body.id,-1):
            world.hit_enemy(body,4*count)
            self.weapon._line_hits[body.id]=world.time+.4
        return True  # The enemy must not reflect the same normal a second time.

    def damage(self,world,amount):return 0.
    def draw(self,graphics,surface,world):pass  # TailImage draws the whole polyline once.
