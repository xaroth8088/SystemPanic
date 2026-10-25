"""Twin salvo bolts wrap once, optionally guide, and own their contacts."""
import math
import pygame
from system_panic.model import Vec,WIDTH,HEIGHT,normalized,circle_rect
from system_panic.pak_api import ProjectileBase

class SalvoBolt(ProjectileBase):
    def __init__(self,world,weapon,direction,side,guided):
        side_vector=Vec(-direction.y,direction.x)*side
        super().__init__(world.player.pos+direction*20+side_vector,direction*550,4)
        self.weapon,self.guided=weapon,guided
        self.remaining=3.
        self.wrapped=False
    def update(self,world,dt):
        self.remaining-=dt
        if self.remaining<=0:
            self.alive=False
            return
        targets=[e for e in world.enemies if e.health>0]
        if self.guided and targets:
            target=min(targets,key=lambda e:e.pos.distance_squared_to(self.pos))
            self.vel=normalized(self.vel.lerp(normalized(target.pos-self.pos)*550,min(1,dt*3)))*550
        self.pos+=self.vel*dt
        if not (0<self.pos.x<WIDTH and 0<self.pos.y<HEIGHT):
            if self.wrapped:
                self.alive=False
                return
            self.wrapped=True
            self.pos.x%=WIDTH
            self.pos.y%=HEIGHT
        for wall in world.cover:
            if wall.health>0 and circle_rect(self.pos,self.radius,wall.rect):
                wall.health-=23
                self.alive=False
                return
        for enemy in targets:
            if enemy.pos.distance_to(self.pos)<enemy.radius+self.radius:
                world.hit_enemy(enemy,23)
                self.alive=False
                return
    def draw(self,graphics,surface,world):
        color=world.pak("weapon").color
        image=graphics.render_sprite(self.weapon.sprite(world,self),24,color)
        image=pygame.transform.rotate(image,-math.degrees(math.atan2(self.vel.y,self.vel.x))-90)
        surface.blit(image,image.get_rect(center=self.pos))
