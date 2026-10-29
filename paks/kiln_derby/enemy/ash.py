"""Only active moving ash hurts; no advance target circles or windup graphics."""
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT
from system_panic.pak_api import ProjectileBase


class Ash(ProjectileBase):
    def __init__(self, position, heading, damage):
        super().__init__(position, heading*175, 7)
        self.damage = damage
        self.age = 0.

    def update(self, world, dt):
        self.age += dt
        previous = self.pos.copy()
        self.pos += self.vel*dt
        if self.age > 3 or not 0 < self.pos.x < WIDTH or not 0 < self.pos.y < HEIGHT or world.segment_blocked(previous,self.pos,self):
            self.alive = False
            return
        if world.player.overlaps_circle(self.pos,self.radius):
            world.hit_player(self.damage)
            self.alive = False

    def is_threat_to(self, world, body):
        return body is world.player

    def draw(self, graphics, surface, world):
        pygame.draw.circle(surface,(115,51,37),self.pos,9)
        pygame.draw.circle(surface,(255,141,77),self.pos,6)
        pygame.draw.circle(surface,(255,219,151),self.pos,2)
