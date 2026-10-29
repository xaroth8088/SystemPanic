"""A floating paper seal; captures its own media and survives later swaps."""
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
        if delta.length_squared() < 180**2:
            world.move_body(self, normalized(delta)*150*dt, self.radius)
        else:
            world.move_body(self, Vec(math.cos(self.age*2)*8, math.sin(self.age*2)*6)*dt, self.radius)
        if self.pos.distance_to(world.player.pos) < self.radius+world.player.radius+5:
            if world.collect_powerup(self) and self.chime is not None: self.chime.play(volume=.45)

    def draw(self, graphics, surface, world):
        points = [self.pos+Vec(14, 0).rotate(45+turn*90) for turn in range(4)]
        pygame.draw.polygon(surface, self.color, points, 2)
        image = graphics.render_sprite(self.art.frame(int(self.age*7)%4, columns=4), 20, self.color)
        surface.blit(image, image.get_rect(center=self.pos))
