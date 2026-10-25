"""A harpoon catches, reels and finishes a target; no host grapple rules."""
import math
import pygame
from system_panic.model import Vec,WIDTH,HEIGHT,normalized,circle_rect
from system_panic.pak_api import ProjectileBase

class Harpoon(ProjectileBase):
    def __init__(self,world,weapon,direction):
        super().__init__(world.player.pos+direction*20,direction*650,5)
        self.weapon=weapon
        self.target=None
        self.returning=False
        self.remaining=3.
    def update(self,world,dt):
        self.remaining-=dt
        if self.remaining<=0:
            self.alive=False
            return
        if self.target is not None:
            if self.target.health<=0 or self.target not in world.enemies:
                self.target=None
                self.returning=True
            else:
                self.target.pos+=(world.player.pos-self.target.pos)*min(1,dt*4)
                self.pos=self.target.pos.copy()
                if self.pos.distance_to(world.player.pos)<32:
                    world.hit_enemy(self.target,38)
                    self.alive=False
                return
        if self.returning:
            delta=world.player.pos-self.pos
            if delta.length()<20:
                self.alive=False
                return
            self.vel=normalized(delta)*750
        self.pos+=self.vel*dt
        if not (4<self.pos.x<WIDTH-4 and 4<self.pos.y<HEIGHT-4): self.returning=True
        if not self.returning:
            for wall in world.cover:
                if wall.health>0 and circle_rect(self.pos,self.radius,wall.rect):
                    world.hit_cover(wall,40)
                    self.returning=True
                    return
            for enemy in world.enemies:
                if enemy.health>0 and enemy.pos.distance_to(self.pos)<enemy.radius+self.radius:
                    world.hit_enemy(enemy,18)
                    self.target=enemy
                    return
    def draw(self,graphics,surface,world):
        color=world.pak("weapon").color
        pygame.draw.line(surface,tuple(int(c*.55) for c in color),world.player.pos,self.pos,1)
        image=graphics.render_sprite(self.weapon.sprite(world,self),29,color)
        image=pygame.transform.rotate(image,-math.degrees(math.atan2(self.vel.y,self.vel.x)))
        surface.blit(image,image.get_rect(center=self.pos))
