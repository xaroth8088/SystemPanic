"""A short single-target bite, rather than a screen-wide damage wave."""
import math
import pygame
from system_panic.model import Vec, normalized
from system_panic.pak_api import ProjectileBase


class ChompBite(ProjectileBase):
    def __init__(self, world, weapon, direction):
        super().__init__(world.player.pos, Vec(), 12)
        self.weapon = weapon
        self.direction = direction.copy()
        self.remaining = .16
        self.hit = False

    def update(self, world, dt):
        self.remaining -= dt
        self.radius = min(70., self.radius + 420 * dt)
        self.alive = self.remaining > 0
        if not self.alive or self.hit:
            return
        candidates = []
        for enemy in world.enemies:
            delta = enemy.pos - self.pos
            if (enemy.health > 0 and delta.length() < self.radius + enemy.radius
                    and normalized(delta).dot(self.direction) > .7
                    and not any(w.health > 0 and w.rect.clipline(self.pos, enemy.pos) for w in world.cover)):
                candidates.append(enemy)
        if candidates:
            target = min(candidates, key=lambda e: e.pos.distance_squared_to(self.pos))
            world.hit_enemy(target, 16)
            self.hit = True

    def draw(self, graphics, surface, world):
        angle = -math.atan2(self.direction.y, self.direction.x)
        rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        rect.center = self.pos
        pygame.draw.arc(surface, world.pak("weapon").color, rect, angle - .7, angle + .7, 3)
        image = graphics.render_sprite(self.weapon.sprite(world, self), 22, world.pak("weapon").color)
        point = self.pos + self.direction * self.radius
        surface.blit(image, image.get_rect(center=point))
