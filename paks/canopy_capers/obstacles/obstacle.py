"""One-way living branches: springs launch every actor; leaves collapse/regrow."""
import math
import random
import pygame
from system_panic.model import Cover, Vec, FIXED_DT
from system_panic.pak_api import ObstaclesBase


class Branch(Cover):
    def __init__(self, rect, kind):
        super().__init__(pygame.Rect(rect), 100., 100.)
        self.kind, self.loaded, self.missing, self.flex = kind, 0., 0., 0.
        self.cooldowns = {}

    def blocks_body(self, body):
        return (self.missing <= 0 and body is not None and body.vel.y >= 0
                and body.pos.y + body.radius <= self.rect.top + body.vel.y * FIXED_DT + .1)

    def blocks_projectile(self, projectile):
        return False

    def on_contact(self, world, body, normal):
        if normal.y < 0 and self.kind == "spring" and body.vel.y >= 0:
            body.vel.y = -475
            self.flex = .25
            world.burst(Vec(body.pos.x, self.rect.top), (211, 248, 126), 4)
            return True
        return False


class Obstacles(ObstaclesBase):
    def init(self):
        self.art = self.load_asset("obstacles_sheet.png")
        self.tiles = {}

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0) * 5) % 4, columns=4)

    def build(self, world):
        rng = random.Random(f"{world.seed}:canopy_capers:{world.wave}")
        offset = rng.randint(-24, 24)
        # Low staggered steps are reachable with one jump; no closed cavities.
        locations = ((170, 390), (400, 318), (650, 390), (805, 312), (555, 240))
        return [Branch((x - 67 + offset + rng.randint(-8, 8), y + rng.randint(-3, 3),
                        rng.randint(124, 146), 14), "spring" if (i + world.wave) % 3 == 0 else "leaf")
                for i, (x, y) in enumerate(locations)]

    def take_damage(self, world, obstacle, damage):
        # Leaves are temporary footing, not destructible walls.
        if obstacle.kind == "leaf" and damage > 0:
            obstacle.loaded = min(.8, obstacle.loaded + damage / 180)
        return 0.

    def update(self, world, dt):
        actors = (world.player, *world.enemies)
        for wall in world.cover:
            wall.flex = max(0., wall.flex - dt)
            if wall.missing > 0:
                wall.missing = max(0., wall.missing - dt)
                # Delay reappearance while someone crosses its footprint.
                if wall.missing <= 0 and any(wall.overlaps_circle(b.pos, b.radius + 3) for b in actors):
                    wall.missing = .1
                continue
            occupied = any(abs(b.pos.y + b.radius - wall.rect.top) < 4
                           and wall.rect.left - b.radius < b.pos.x < wall.rect.right + b.radius for b in actors)
            if wall.kind == "leaf":
                wall.loaded = max(0., wall.loaded + dt * (1 if occupied else -.6))
                if wall.loaded >= .8:
                    wall.loaded, wall.missing = 0., 2.4
                    world.burst(Vec(wall.rect.center), (183, 235, 103), 8)

    def draw(self, graphics, surface, world, wall):
        if wall.missing > 0:
            return
        color = (238, 201, 108) if wall.kind == "spring" else (139, 191, 84)
        rect = wall.rect
        pygame.draw.rect(surface, (40, 60, 30), rect, border_radius=6)
        frame = self.sprite(world)
        key = (frame.rect, rect.width)
        if key not in self.tiles:
            pixels = frame.image.surface.subsurface(frame.rect)
            opaque = pixels.get_bounding_rect(min_alpha=100)
            tile = pixels.subsurface(opaque) if opaque.width and opaque.height else pixels
            height = max(22, min(38, round(tile.get_height() * rect.width / tile.get_width())))
            self.tiles[key] = pygame.transform.scale(tile, (rect.width, height))
        image = self.tiles[key]
        surface.blit(image, image.get_rect(midtop=rect.midtop))
        pygame.draw.line(surface, color, rect.topleft, rect.topright, 2)
        if wall.kind == "spring":
            for x in range(rect.left + 8, rect.right - 5, 17):
                pygame.draw.lines(surface, color, False, ((x, rect.bottom), (x + 5, rect.bottom + 5), (x + 10, rect.bottom)), 1)
