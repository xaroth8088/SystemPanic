"""Bomb behavior is local to this Pak, including motion and hit policy."""
import math
import pygame
from system_panic.model import WIDTH, HEIGHT, normalized, circle_rect
from system_panic.pak_api import ProjectileBase


class Bomb(ProjectileBase):
    def __init__(self, world, weapon, direction):
        super().__init__(world.player.pos + direction * 19, direction * 380, 7)
        self._weapon = weapon
        self._remaining = 3.
        self._damage = 58

    def update(self, world, dt):
        self._remaining -= dt
        if self._remaining <= 0:
            self.alive = False
            return
        if world.prefs.aim_assist and world.enemies:
            target = min(world.enemies, key=lambda enemy: enemy.pos.distance_squared_to(self.pos))
            desired = normalized(target.pos - self.pos) * 380
            self.vel = self.vel.lerp(desired, min(1, dt * 2.2))
        self.pos += self.vel * dt
        if not (4 <= self.pos.x <= WIDTH - 4 and 4 <= self.pos.y <= HEIGHT - 4):
            self.alive = False
            return
        for obstacle in world.cover:
            if obstacle.health <= 0 or not circle_rect(self.pos, self.radius, obstacle.rect):
                continue
            obstacle.health -= self._damage
            self.explode(world)
            self.alive = False
            return
        for enemy in world.enemies:
            if enemy.health <= 0:
                continue
            if enemy.pos.distance_to(self.pos) >= enemy.radius + self.radius:
                continue
            world.hit_enemy(enemy, self._damage)
            self.explode(world)
            self.alive = False
            return

    def explode(self, world):
        for enemy in world.enemies:
            if enemy.health > 0 and enemy.pos.distance_to(self.pos) < 85 + enemy.radius:
                world.hit_enemy(enemy, self._damage * .7)
        for obstacle in world.cover:
            if circle_rect(self.pos, 85, obstacle.rect):
                obstacle.health -= self._damage
        world.burst(self.pos, world.pak("weapon").color, 20)
        world.shake = max(world.shake, 3)

    def draw(self, graphics, surface, world):
        color = world.pak("weapon").color
        pygame.draw.line(surface, tuple(int(c * .45) for c in color), self.pos - self.vel * .022, self.pos, 3)
        image = graphics.render_sprite(self._weapon.sprite(world, self), 27, color)
        image = pygame.transform.rotate(image, -math.degrees(math.atan2(self.vel.y, self.vel.x)))
        surface.blit(image, image.get_rect(center=self.pos))
