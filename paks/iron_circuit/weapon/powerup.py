"""iron_circuit: a local collectible with its own motion and pickup policy."""
import math
import pygame
from system_panic.model import Vec,WIDTH,HEIGHT,normalized
from system_panic.pak_api import PowerupBase


class IronCircuitPowerup(PowerupBase):
    def __init__(self,position,art,color):
        super().__init__(position,10)
        self.art,self.color=art,color
        self.age=0.
        self.vel=Vec(115,0).rotate((position.x*.3)%360)

    def update(self,world,dt):
        if not self.alive:return
        self.age+=dt
        if self.age>50:
            self.alive=False
            return
        motion=world.move_body(self,self.vel*dt,self.radius)
        for normal in motion.normals:
            self.vel-=normal*(2*self.vel.dot(normal))
        if self.pos.distance_to(world.player.pos)<=self.radius+world.player.radius+3:
            world.collect_powerup(self)

    def draw(self,graphics,surface,world):
        radius=12+int(2*math.sin(self.age*5))
        pygame.draw.circle(surface,self.color,self.pos,radius,2)
        image=graphics.render_sprite(self.art,16,self.color)
        surface.blit(image,image.get_rect(center=self.pos))
        pygame.draw.line(surface,(240,245,210),self.pos+Vec(-3,-17),self.pos+Vec(3,-17),2)
        pygame.draw.line(surface,(240,245,210),self.pos+Vec(0,-20),self.pos+Vec(0,-14),2)
