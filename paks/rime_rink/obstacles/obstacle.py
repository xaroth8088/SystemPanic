"""Warm strips brake actors; mobile ice presses shove and damage both teams."""
import math
import random
import pygame
from system_panic.model import Cover, Vec
from system_panic.pak_api import ObstaclesBase


class RinkShape(Cover):
    def __init__(self, rect, kind, phase=0.):
        super().__init__(pygame.Rect(rect), 100., 100.)
        self.kind, self.phase = kind, phase
        self.home = Vec(self.rect.center)
        self.age = 0.
        self.hits = {}
        if kind == "press":
            # Spawn/relocation must see the same phase used on the first tick.
            self.rect.centerx = round(self.home.x + math.sin(self.phase) * 82)

    def blocks_body(self, body):
        return self.kind == "press"

    def blocks_projectile(self, projectile):
        return self.kind == "press"


class Obstacles(ObstaclesBase):
    def init(self):
        self.art = self.load_asset("obstacles_sheet.png")

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0) * 5) % 4, columns=4)

    def build(self, world):
        rng = random.Random(f"{world.seed}:rime_rink:{world.wave}")
        shapes = [RinkShape((x + rng.randrange(-20, 21), y + rng.randrange(-18, 19), 70, 48), "press", rng.random() * math.tau)
                  for x, y in ((285, 120), (625, 305))]
        shapes += [RinkShape((x + rng.randrange(-15, 16), 55, 50, 370), "warm") for x in (160, 760)]
        return shapes

    def take_damage(self, world, obstacle, damage):
        return 0.

    def update(self, world, dt):
        actors = (world.player, *world.enemies)
        for wall in world.cover:
            wall.age += dt
            if wall.kind == "warm":
                for body in actors:
                    if wall.rect.collidepoint(body.pos):
                        body.vel *= math.exp(-4 * dt)
                continue
            old_center = Vec(wall.rect.center)
            wall.rect.centerx = round(wall.home.x + math.sin(wall.age * .9 + wall.phase) * 82)
            movement = Vec(wall.rect.center) - old_center
            for body in actors:
                if body.health <= 0 or not wall.overlaps_circle(body.pos, body.radius + 1):
                    continue
                side = 1 if body.pos.x >= wall.rect.centerx else -1
                desired = Vec(wall.rect.centerx + side * (wall.rect.width / 2 + body.radius + 4), body.pos.y)
                body.pos = world.safe_position(desired, body.radius + 1, body=body)
                body.vel.x = side * max(100, abs(movement.x) / max(dt, .001))
                identity = id(body)
                if wall.hits.get(identity, -10.) <= wall.age - .7:
                    if body is world.player:
                        world.hit_player(9 + world.wave * .35)
                    else:
                        world.hit_enemy(body, 24 + world.wave * 1.2)
                    wall.hits[identity] = wall.age
                    world.burst(body.pos, (190, 239, 255), 5)
            # Bound per-body cooldown storage as dead bodies disappear.
            active = {id(b) for b in actors}
            wall.hits = {identity: age for identity, age in wall.hits.items() if identity in active}

    def draw_floor(self, graphics, surface, world):
        for wall in world.cover:
            if wall.kind == "warm":
                pygame.draw.rect(surface, (51, 38, 30), wall.rect, border_radius=6)
                for y in range(wall.rect.top + 6, wall.rect.bottom - 3, 12):
                    pygame.draw.line(surface, (160, 100, 62), (wall.rect.left + 5, y), (wall.rect.right - 5, y), 2)
            else:
                pygame.draw.line(surface, (40, 67, 82), (wall.home.x - 90, wall.home.y), (wall.home.x + 90, wall.home.y), 5)

    def draw(self, graphics, surface, world, wall):
        if wall.kind == "warm":
            return
        pygame.draw.rect(surface, (35, 65, 86), wall.rect, border_radius=7)
        pygame.draw.rect(surface, (142, 221, 250), wall.rect, 2, border_radius=7)
        image = graphics.render_sprite(self.sprite(world), 56, (132, 215, 255))
        surface.blit(image, image.get_rect(center=wall.rect.center))
