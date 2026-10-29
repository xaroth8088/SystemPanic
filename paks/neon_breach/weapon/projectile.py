"""Accelerating pinball with local bounce, paddle reflection and hit clocks."""
import math
import pygame
from system_panic.model import Vec,WIDTH,HEIGHT,normalized,circle_rect
from system_panic.pak_api import ProjectileBase

class PlasmaBall(ProjectileBase):
    def __init__(self,world,weapon,direction):
        super().__init__(world.player.pos+direction*24,direction*420,8)
        self.weapon=weapon
        self.remaining=10.
        self.hits={}
        self.guided=False
        self.energy=1.2
        self.paddle_lock=0.

    def update(self,world,dt):
        self.remaining-=dt
        self.paddle_lock=max(0.,self.paddle_lock-dt)
        self.hits={id:time-dt for id,time in self.hits.items() if time>dt}
        if self.remaining<=0:
            self.alive=False
            return
        old=self.pos.copy()
        self.pos+=self.vel*dt
        delta=self.pos-world.player.pos
        if not self.paddle_lock and world.player.overlaps_circle(self.pos,self.radius+5) and self.vel.dot(delta)<0:
            p=world.player.pos
            normal=(Vec(0,-1) if p.y<32 else Vec(1,0) if p.x>WIDTH-32 else
                    Vec(0,1) if p.y>HEIGHT-32 else Vec(-1,0) if p.x<32 else
                    normalized(p-Vec(WIDTH/2,HEIGHT/2)))
            tangent=Vec(-normal.y,normal.x)
            offset=max(-.7,min(.7,delta.dot(tangent)/32+world.player.vel.dot(tangent)/900))
            inward=(-normal+tangent*offset).normalize()
            self.vel=inward*min(760,self.vel.length()+65)
            self.energy=min(2.4,self.energy+.65)
            self.remaining=min(12.,self.remaining+2.)
            self.weapon.returns+=1
            self.paddle_lock=.2
            world.burst(self.pos,world.pak('weapon').color,5)
        for axis,extent in ((0,WIDTH),(1,HEIGHT)):
            if self.pos[axis]<self.radius or self.pos[axis]>extent-self.radius:
                self.pos[axis]=max(self.radius,min(extent-self.radius,self.pos[axis]))
                self.vel[axis]*=-1
                self.energy-=.35
        if self.energy<.25:
            self.alive=False
            return
        for wall in world.geometry:
            if wall.health>0 and wall.blocks_projectile(self) and wall.overlaps_circle(self.pos, self.radius):
                world.hit_cover(wall,(20+6*world.powerups_collected)*self.energy)
                if old.x<wall.rect.left or old.x>wall.rect.right: self.vel.x*=-1
                else: self.vel.y*=-1
                self.pos=old
                break
        for enemy in world.enemies:
            if enemy.health>0 and enemy.id not in self.hits and self.pos.distance_to(enemy.pos)<self.radius+enemy.radius:
                world.hit_enemy(enemy,(20+6*world.powerups_collected)*self.energy)
                self.hits[enemy.id]=.16
                normal=normalized(self.pos-enemy.pos)
                if self.vel.dot(normal)<0: self.vel=self.vel.reflect(normal)
                self.vel=normalized(self.vel)*min(760,self.vel.length()+25)

    def draw(self,graphics,surface,world):
        image=graphics.render_sprite(self.weapon.sprite(world,self),25,world.pak("weapon").color)
        pygame.draw.circle(surface,(255,160,225),self.pos,int(10+self.energy*2),1)
        surface.blit(image,image.get_rect(center=self.pos))
