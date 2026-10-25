"""This Pak owns hostile-shot motion, damage and presentation."""
import pygame
from system_panic.model import WIDTH, HEIGHT, circle_rect
from system_panic.pak_api import ProjectileBase


class HostileShot(ProjectileBase):
    def __init__(self, position, velocity, damage):
        super().__init__(position, velocity, 5)
        self._remaining = 7.
        self._damage = damage

    def update(self, world, dt):
        self._remaining -= dt
        self.pos += self.vel * dt
        if self._remaining <= 0 or not (4 <= self.pos.x <= WIDTH - 4 and 4 <= self.pos.y <= HEIGHT - 4):
            self.alive = False
            return
        if any(obstacle.health > 0 and obstacle.blocks_projectile(self) and obstacle.overlaps_circle(self.pos, self.radius) for obstacle in world.geometry):
            self.alive = False
            return
        if self.pos.distance_to(world.player.pos) < world.player.radius + self.radius:
            world.hit_player(self._damage)
            self.alive = False

    def draw(self, graphics, surface, world):
        pygame.draw.circle(surface, (255, 91, 117), self.pos, 5)
        pygame.draw.circle(surface, (255, 220, 225), self.pos, 2)

    def is_threat_to(self, world, body):
        return body is world.player
