"""An overhead sword sweep and one physically recoverable thrown blade."""
import math
import pygame
from system_panic.model import Vec,WIDTH,HEIGHT,normalized
from system_panic.pak_api import ProjectileBase

class Swing(ProjectileBase):
    def __init__(self,world,weapon,direction):
        super().__init__(world.player.pos,Vec(),5)
        self.weapon,self.direction=weapon,direction.copy()
        self.remaining=.22;self.hit_ids=set();self._guided=False
        self.facing=1 if direction.x>=0 else -1
        self.angle=-math.pi*.85
        self._damage=25+6*world.powerups_collected
        self.reach=72+min(36,4*world.powerups_collected)
    def update(self,world,dt):
        if not self.alive:return
        before=self.angle
        self.remaining=max(0.,self.remaining-dt)
        self.angle=-math.pi*.85+math.pi*1.1*(1-self.remaining/.22)
        self.pos=world.player.pos.copy()
        count=max(1,math.ceil(abs(self.angle-before)/.08))
        for sample in range(count+1):
            angle=before+(self.angle-before)*sample/count
            ray=Vec(math.cos(angle)*self.facing,math.sin(angle));end=self.pos+ray*self.reach
            for step in range(1,math.ceil(self.reach/4)+1):
                point=self.pos+ray*min(self.reach,step*4)
                walls=[w for w in world.geometry if w.health>0 and w.blocks_projectile(self) and w.overlaps_circle(point,5)]
                if walls:
                    end=point
                    for wall in walls:world.hit_cover(wall,self._damage*dt/.22/(count+1))
                    break
            edge=end-self.pos
            for enemy in world.enemies:
                if enemy.health<=0 or enemy.id in self.hit_ids:continue
                t=max(0.,min(1.,(enemy.pos-self.pos).dot(edge)/max(.01,edge.length_squared())))
                if (self.pos+edge*t).distance_to(enemy.pos)<enemy.radius+7:
                    applied=world.hit_enemy(enemy,self._damage);self.hit_ids.add(enemy.id)
                    if applied and enemy.health>0:
                        push=normalized(enemy.pos-self.pos,Vec(self.facing,0))
                        world.move_body(enemy,push*28,enemy.radius)
                        enemy.vel+=push*95
        if self.remaining<=0:self.alive=False
    def draw(self,graphics,surface,world):
        ray=Vec(math.cos(self.angle)*self.facing,math.sin(self.angle))
        image=graphics.render_sprite(self.weapon.sprite(world,self),int(self.reach),world.pak('weapon').color)
        image=pygame.transform.rotate(image,-math.degrees(math.atan2(ray.y,ray.x)))
        surface.blit(image,image.get_rect(center=self.pos+ray*self.reach*.55))

class Sword(ProjectileBase):
    def __init__(self,world,weapon,direction,strength):
        super().__init__(world.player.pos+direction*30,direction*(620+220*strength)+world.player.vel*.2,7)
        self.weapon=weapon;self.state='flying';self.age=0.;self.pickup_lock=.25
        self._damage=90+50*strength+18*world.powerups_collected;self._guided=False
    def update(self,world,dt):
        self.age+=dt;self.pickup_lock=max(0.,self.pickup_lock-dt)
        if self.state=='flying':
            self.vel.y+=160*dt
            steps=max(1,math.ceil(self.vel.length()*dt/4))
            for _ in range(steps):
                old=self.pos.copy();self.pos+=self.vel*dt/steps
                walls=[w for w in world.geometry if w.health>0 and w.blocks_projectile(self) and w.overlaps_circle(self.pos,self.radius)]
                edge=not(self.radius<self.pos.x<WIDTH-self.radius and self.radius<self.pos.y<HEIGHT-self.radius)
                if walls or edge or self.age>1.6:
                    for wall in walls:world.hit_cover(wall,self._damage)
                    self.pos=old;self.drop();break
                enemy=next((e for e in world.enemies if e.health>0 and e.pos.distance_to(self.pos)<e.radius+self.radius),None)
                if enemy is not None:
                    world.hit_enemy(enemy,self._damage);world.burst(enemy.pos,world.pak('weapon').color,10)
                    self.drop();break
        else:
            self.vel.y+=550*dt;self.vel.x*=math.exp(-4*dt)
            motion=world.move_body(self,self.vel*dt,self.radius)
            for normal in motion.normals:
                if self.vel.dot(normal)<0:self.vel-=normal*self.vel.dot(normal)
            if self.pickup_lock<=0 and self.pos.distance_to(world.player.pos)<world.player.radius+20 and not any(w.health>0 and w.blocks_body(world.player) and w.overlaps_segment(world.player.pos,self.pos) for w in world.geometry):
                self.alive=False;self.weapon.reclaim(self)
    def drop(self):
        self.state='resting';self.vel=Vec();self.pickup_lock=.22
    def draw(self,graphics,surface,world):
        color=world.pak('weapon').color
        if self.state=='resting':pygame.draw.circle(surface,(255,215,140),self.pos,int(15+2*math.sin(world.time*7)),1)
        image=graphics.render_sprite(self.weapon.sprite(world,self),44,color)
        angle=-math.degrees(math.atan2(self.vel.y,self.vel.x)) if self.state=='flying' else 25
        image=pygame.transform.rotate(image,angle)
        if self.state=='resting':
            image=image.subsurface(image.get_bounding_rect(min_alpha=16))
            surface.blit(image,image.get_rect(midbottom=(self.pos.x,self.pos.y+self.radius)))
        else:surface.blit(image,image.get_rect(center=self.pos))
