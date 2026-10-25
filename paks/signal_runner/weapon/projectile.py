"""Pulse behavior is local to this Pak, including motion and hit policy."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT, circle_rect
from system_panic.pak_api import ProjectileBase


class Pulse(ProjectileBase):
    def __init__(self, world, weapon, direction):
        super().__init__(world.player.pos + direction * 19, direction * 520, 4)
        self._weapon = weapon
        self._remaining = 3.
        self._damage = 16 + 4 * world.powerups_collected

    def update(self, world, dt):
        self._remaining -= dt
        if self._remaining <= 0:
            self.alive = False
            return
        self.pos += self.vel * dt
        if not (4 <= self.pos.x <= WIDTH - 4 and 4 <= self.pos.y <= HEIGHT - 4):
            self.alive = False
            return
        for obstacle in world.geometry:
            if obstacle.health <= 0 or not (obstacle.blocks_projectile(self) and obstacle.overlaps_circle(self.pos, self.radius)):
                continue
            world.hit_cover(obstacle, self._damage)
            self.alive = False
            return
        for enemy in world.enemies:
            if enemy.health <= 0:
                continue
            if enemy.pos.distance_to(self.pos) >= enemy.radius + self.radius:
                continue
            world.hit_enemy(enemy, self._damage)
            self.alive = False
            return

    def draw(self, graphics, surface, world):
        color = world.pak("weapon").color
        pygame.draw.line(surface, tuple(int(c * .45) for c in color), self.pos - self.vel * .022, self.pos, 3)
        image = graphics.render_sprite(self._weapon.sprite(world, self), 21, color)
        image = pygame.transform.rotate(image, -math.degrees(math.atan2(self.vel.y, self.vel.x)))
        surface.blit(image, image.get_rect(center=self.pos))
