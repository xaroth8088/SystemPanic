"""A captured component-local reward survives weapon replacement."""
import math
import pygame
from system_panic.model import Vec, normalized
from system_panic.pak_api import PowerupBase


class Upgrade(PowerupBase):
    def __init__(self,position,art,color,chime):
        super().__init__(position,10)
        self.art,self.color,self.chime,self.age=art,color,chime,0.

    def update(self,world,dt):
        if not self.alive:
            return
        self.age += dt
        if self.age >= 50:
            self.alive=False
            return
        delta=world.player.pos-self.pos
        if delta.length()<155:
            world.move_body(self,normalized(delta)*155*dt,self.radius)
        if self.pos.distance_to(world.player.pos)<self.radius+world.player.radius+4:
            if world.collect_powerup(self):
                self.chime.play(volume=.45)

    def draw(self,graphics,surface,world):
        pygame.draw.circle(surface,self.color,self.pos,13+int(2*math.sin(self.age*5)),2)
        image=graphics.render_sprite(self.art.frame(int(self.age*7)%4,columns=4),22,self.color)
        surface.blit(image,image.get_rect(center=self.pos))
