"""Only active Pak-owned hazards are drawn; delayed damage timing stays local."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT
from system_panic.pak_api import ProjectileBase




class Bolt(ProjectileBase):
    def __init__(self, position, velocity, damage, radius=4):
        super().__init__(position,velocity,radius)
        self.damage,self.age=damage,0.
        self.bounces=16

    def update(self, world, dt):
        # Small swept steps prevent a fast bolt tunnelling through thin mirrors
        # or the pilot. Only projectile-blocking shapes reflect these shots.
        remaining=min(dt,max(0.,6-self.age))
        self.age+=dt
        steps=max(1,math.ceil(self.vel.length()*remaining/2))
        step=remaining/steps
        for _ in range(steps):
            previous=self.pos.copy()
            candidate=self.pos+self.vel*step
            for axis,limit in ((0,WIDTH),(1,HEIGHT)):
                if candidate[axis]<self.radius:
                    candidate[axis]=2*self.radius-candidate[axis]
                    self.vel[axis]=abs(self.vel[axis])
                    self.bounces-=1
                elif candidate[axis]>limit-self.radius:
                    candidate[axis]=2*(limit-self.radius)-candidate[axis]
                    self.vel[axis]=-abs(self.vel[axis])
                    self.bounces-=1
            for wall in world.geometry:
                if wall.health<=0 or not wall.blocks_projectile(self) or not wall.overlaps_circle(candidate,self.radius):continue
                x_hit=wall.overlaps_circle(Vec(candidate.x,previous.y),self.radius)
                y_hit=wall.overlaps_circle(Vec(previous.x,candidate.y),self.radius)
                if x_hit and not y_hit:
                    normal=Vec(-1 if self.vel.x>0 else 1,0)
                elif y_hit and not x_hit:
                    normal=Vec(0,-1 if self.vel.y>0 else 1)
                else:
                    distances=(abs(candidate.x-wall.rect.left),abs(candidate.x-wall.rect.right),abs(candidate.y-wall.rect.top),abs(candidate.y-wall.rect.bottom))
                    normal=(Vec(-1,0),Vec(1,0),Vec(0,-1),Vec(0,1))[distances.index(min(distances))]
                if self.vel.dot(normal)<0:
                    self.vel-=2*normal*self.vel.dot(normal)
                candidate=previous
                self.bounces-=1
                world.hit_cover(wall,self.damage)
                break
            self.pos=candidate
            if self.pos.distance_to(world.player.pos)<world.player.radius+self.radius:
                world.hit_player(self.damage)
                self.alive=False
                return
            if self.bounces<0:
                self.alive=False
                return
        if self.age>=6:self.alive=False

    def is_threat_to(self, world, body):
        return body is world.player

    def draw(self, graphics, surface, world):
        pygame.draw.line(surface,(125,65,95),self.pos-self.vel*.04,self.pos,3)
        pygame.draw.circle(surface,(255,140,165),self.pos,self.radius)
        pygame.draw.circle(surface,(255,235,215),self.pos,2)


class Zone(ProjectileBase):
    def __init__(self, position, radius, delay, damage, duration=.35):
        super().__init__(position,Vec(),radius)
        self.delay,self.damage,self.duration,self.age=delay,damage,duration,0.

    def update(self, world, dt):
        self.age+=dt
        if self.age>=self.delay:
            if self.pos.distance_to(world.player.pos)<self.radius+world.player.radius:
                world.hit_player(self.damage)
            if self.age>self.delay+self.duration:self.alive=False

    def is_threat_to(self, world, body):
        return body is world.player

    def draw(self, graphics, surface, world):
        if self.age<self.delay:return
        pygame.draw.circle(surface,(255,115,160),self.pos,int(self.radius),3)
        pygame.draw.line(surface,(255,150,190),self.pos-Vec(8,8),self.pos+Vec(8,8),2)
        pygame.draw.line(surface,(255,150,190),self.pos-Vec(-8,8),self.pos+Vec(-8,8),2)
