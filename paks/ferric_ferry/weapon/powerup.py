"""Induction module pickup with captured local art/chime and finite lifetime."""
import math
import pygame
from system_panic.model import Vec, normalized
from system_panic.pak_api import PowerupBase


class Upgrade(PowerupBase):
    def __init__(self, position, art, color, chime=None):
        super().__init__(position, 10)
        self.art, self.color, self.chime = art, color, chime
        self.age = 0.

    def update(self, world, dt):
        if not self.alive: return
        self.age += dt
        if self.age >= 50:
            self.alive = False
            return
        delta = world.player.pos-self.pos
        if delta.length_squared() < 230**2:
            self.vel = self.vel.lerp(normalized(delta)*170, min(1., dt*6))
        else:
            self.vel *= math.exp(-3*dt)
        world.move_body(self, self.vel*dt, self.radius)
        if self.pos.distance_to(world.player.pos) < self.radius+world.player.radius+4:
            if world.collect_powerup(self) and self.chime is not None: self.chime.play(volume=.45)

    def draw(self, graphics, surface, world):
        pygame.draw.circle(surface, self.color, self.pos, 14, 1)
        for index in range(2):
            point = self.pos+Vec(14, 0).rotate(self.age*140+index*180)
            pygame.draw.circle(surface, self.color, point, 3)
        image = graphics.render_sprite(self.art.frame(int(self.age*7)%4, columns=4), 20, self.color)
        surface.blit(image, image.get_rect(center=self.pos))
