"""Glaive behavior is local to this Pak, including motion and hit policy."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT, normalized, circle_rect
from system_panic.pak_api import ProjectileBase


class Glaive(ProjectileBase):
    def __init__(self, world, weapon, direction,boost=1.):
        super().__init__(world.player.pos + direction * 19, direction * (600 + min(160,20*world.powerups_collected)), 7)
        self._weapon = weapon
        self._remaining = 3.
        self._damage = (28+5*world.powerups_collected)*boost
        self._outbound = .55 + min(.25,.025*world.powerups_collected)
        self._hits_left = 6
        self._hit_ids = set()
        self._age = 0.
        self.returning=False

    def update(self, world, dt):
        self._remaining -= dt
        if self._remaining <= 0:
            self.alive = False
            return
        self._age += dt
        if self._age > self._outbound:
            if not self.returning:
                self.returning=True
                self._hit_ids.clear()
                self._damage*=1.15
            self.vel = normalized(world.player.pos - self.pos) * 490
            if self.pos.distance_to(world.player.pos) < 16:
                self.alive = False
                self._weapon.caught(world)
                return
        self.pos += self.vel * dt
        for obstacle in world.geometry:
            if self.returning:break
            if obstacle.health <= 0 or not (obstacle.blocks_projectile(self) and obstacle.overlaps_circle(self.pos, self.radius)):
                continue
            world.hit_cover(obstacle, self._damage)
            self.alive = False
            return
        for enemy in world.enemies:
            if enemy.health <= 0:
                continue
            if enemy.id in self._hit_ids:
                continue
            if enemy.pos.distance_to(self.pos) >= enemy.radius + self.radius:
                continue
            world.hit_enemy(enemy, self._damage)
            self._hit_ids.add(enemy.id)
            self._hits_left-=1
            if self._hits_left<=0:
                self.alive = False
                return

    def draw(self, graphics, surface, world):
        color = world.pak("weapon").color
        pygame.draw.line(surface, tuple(int(c * .45) for c in color), self.pos - self.vel * .022, self.pos, 3)
        image = graphics.render_sprite(self._weapon.sprite(world, self), 27, color)
        image = pygame.transform.rotate(image, -math.degrees(math.atan2(self.vel.y, self.vel.x)))
        surface.blit(image, image.get_rect(center=self.pos))
