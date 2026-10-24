"""Ricochet behavior is local to this Pak, including motion and hit policy."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT, circle_rect
from system_panic.pak_api import ProjectileBase


class Ricochet(ProjectileBase):
    def __init__(self, world, weapon, direction):
        super().__init__(world.player.pos + direction * 19, direction * 440, 4)
        self._weapon = weapon
        self._remaining = 3.
        self._damage = 19
        self._bounces_left = 4

    def update(self, world, dt):
        self._remaining -= dt
        if self._remaining <= 0:
            self.alive = False
            return
        self.pos += self.vel * dt
        if not (4 <= self.pos.x <= WIDTH - 4 and 4 <= self.pos.y <= HEIGHT - 4):
            if self._bounces_left > 0:
                if self.pos.x < 4 or self.pos.x > WIDTH - 4:
                    self.vel.x *= -1
                if self.pos.y < 4 or self.pos.y > HEIGHT - 4:
                    self.vel.y *= -1
                self._bounces_left -= 1
                self.pos.x = max(4, min(WIDTH - 4, self.pos.x))
                self.pos.y = max(4, min(HEIGHT - 4, self.pos.y))
            else:
                self.alive = False
                return
        for obstacle in world.cover:
            if obstacle.health <= 0 or not circle_rect(self.pos, self.radius, obstacle.rect):
                continue
            obstacle.health -= self._damage
            if self._bounces_left > 0:
                self.pos -= self.vel * dt * 2
                self.vel *= -1
                self._bounces_left -= 1
                break
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
