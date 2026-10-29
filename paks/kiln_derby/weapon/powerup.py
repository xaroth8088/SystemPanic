"""Captured local art keeps drops valid after weapon replacement."""
import math
import pygame
from system_panic.model import Vec, normalized
from system_panic.pak_api import PowerupBase


class Upgrade(PowerupBase):
    def __init__(self, position, art, color, chime=None):
        super().__init__(position, 10)
        self.chime = chime
        self.art, self.color, self.age = art, color, 0.

    def update(self, world, dt):
        if not self.alive: return
        self.age += dt
        if self.age >= 50:
            self.alive = False
            return
        delta = world.player.pos - self.pos
        if delta.length() < 145:
            world.move_body(self, normalized(delta) * 140 * dt, self.radius)
        if delta.length() < self.radius + world.player.radius + 4:
            if world.collect_powerup(self) and self.chime is not None:
                self.chime.play(volume=.45)

    def draw(self, graphics, surface, world):
        pygame.draw.circle(surface, self.color, self.pos, 13 + int(2 * math.sin(self.age * 5)), 2)
        image = graphics.render_sprite(self.art.frame(int(self.age*6)%4, columns=4), 21, self.color)
        surface.blit(image, image.get_rect(center=self.pos))
