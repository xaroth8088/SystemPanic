"""A growing directional chomp wave, with each hit owned by the Pak."""
import math
import pygame
from system_panic.model import Vec,normalized,circle_rect
from system_panic.pak_api import ProjectileBase

class ChompWave(ProjectileBase):
    def __init__(self,world,weapon,direction):
        super().__init__(world.player.pos,Vec(),1)
        self.weapon=weapon
        self.direction=direction.copy()
        self.hits=set()
        self.walls=set()

    def update(self,world,dt):
        self.radius+=640*dt
        if self.radius>1120:
            self.alive=False
            return
        for enemy in world.enemies:
            delta=enemy.pos-self.pos
            if enemy.health>0 and enemy.id not in self.hits and delta.length()<self.radius+enemy.radius and normalized(delta).dot(self.direction)>.4:
                self.hits.add(enemy.id)
                world.hit_enemy(enemy,27)
        for wall in world.cover:
            if id(wall) not in self.walls and circle_rect(self.pos,self.radius,wall.rect) and normalized(Vec(wall.rect.center)-self.pos).dot(self.direction)>.35:
                wall.health-=27
                self.walls.add(id(wall))

    def draw(self,graphics,surface,world):
        angle=-math.atan2(self.direction.y,self.direction.x)
        rect=pygame.Rect(0,0,self.radius*2,self.radius*2)
        rect.center=self.pos
        pygame.draw.arc(surface,world.pak("weapon").color,rect,angle-.95,angle+.95,3)
        image=graphics.render_sprite(self.weapon.sprite(world,self),25,world.pak("weapon").color)
        point=self.pos+self.direction*self.radius
        surface.blit(image,image.get_rect(center=point))
