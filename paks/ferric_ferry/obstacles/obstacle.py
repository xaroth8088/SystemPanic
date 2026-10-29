"""Shot-reversible magnetic pylons and body-only induction rails."""
import math
import random
import pygame
from system_panic.model import Cover, Vec, normalized
from system_panic.pak_api import ObstaclesBase


class Pylon(Cover):
    def __init__(self, position, polarity):
        super().__init__(pygame.Rect(position[0]-21, position[1]-21, 42, 42), 100, 100)
        self.center = Vec(position)
        self.polarity = polarity
        self.flip_cooldown = 0.
        self.field_radius = 135.

    def overlaps_circle(self, position, radius):
        return self.center.distance_squared_to(position) < (21+radius)**2

    def overlaps_segment(self, start, end):
        a, b = Vec(start), Vec(end)
        delta = b-a
        t = max(0., min(1., (self.center-a).dot(delta)/max(.0001, delta.length_squared())))
        return self.center.distance_squared_to(a+delta*t) < 21**2

    def navigation_key(self):
        return ('ferric-pylon-circle', self.center.x, self.center.y, 21)


class Rail(Cover):
    def blocks_projectile(self, projectile): return False


class FerricObstacles(ObstaclesBase):
    def init(self):
        self.art = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0)*5)%4, columns=4)

    def build(self, world):
        rng = random.Random(f'{world.seed}:ferric_ferry:{world.wave}')
        offset = rng.randrange(-30, 31)
        pylons = [Pylon((230+rng.randrange(-18, 19), 145+offset+rng.randrange(-12, 13)), 1),
                  Pylon((480+rng.randrange(-18, 19), 310-offset+rng.randrange(-12, 13)), -1),
                  Pylon((730+rng.randrange(-18, 19), 145+offset+rng.randrange(-12, 13)), 1)]
        rail_x = rng.randrange(-25, 26)
        rails = [Rail(pygame.Rect(320+rail_x, 85+rng.randrange(-8, 9), 130+rng.randrange(-12, 13), 12), 100, 100),
                 Rail(pygame.Rect(535-rail_x, 390+rng.randrange(-8, 9), 130+rng.randrange(-12, 13), 12), 100, 100)]
        return pylons+rails

    def take_damage(self, world, obstacle, damage):
        if isinstance(obstacle, Pylon) and damage > 0 and obstacle.flip_cooldown <= 0:
            obstacle.polarity *= -1
            obstacle.flip_cooldown = .35
            world.burst(obstacle.center, world.pak('obstacles').color, 5)
        return 0.

    def update(self, world, dt):
        for wall in world.cover:
            if not isinstance(wall, Pylon): continue
            wall.flip_cooldown = max(0., wall.flip_cooldown-dt)
            for body in (world.player, *world.enemies):
                delta = wall.center-body.pos
                distance = delta.length()
                if body.health > 0 and 22 < distance < wall.field_radius:
                    strength = 75*(1-distance/wall.field_radius)
                    force = normalized(delta)*wall.polarity*strength
                    world.move_body(body, force*dt, body.radius)
                    body.vel += force*(dt*.8)
            # Generic physical velocity is public. The projectile remains responsible
            # for its integration, lifetime and combat; stationary regions stay still.
            for shot in tuple(world.projectiles):
                if not shot.alive or shot.vel.length_squared() < 1: continue
                delta = wall.center-shot.pos
                distance = delta.length()
                if 22 < distance < wall.field_radius:
                    old_speed = shot.vel.length()
                    shot.vel += normalized(delta)*(wall.polarity*550*(1-distance/wall.field_radius)*dt)
                    if shot.vel.length_squared() > .001: shot.vel.scale_to_length(old_speed)

    def draw_floor(self, graphics, surface, world):
        for wall in world.cover:
            if not isinstance(wall, Pylon): continue
            color = (52, 65, 79) if wall.polarity > 0 else (65, 53, 67)
            for radius in (52, 86, 122):
                rect = pygame.Rect(0, 0, radius*2, radius*2)
                rect.center = wall.center
                pygame.draw.arc(surface, color, rect, .25, 2.8, 1)
                pygame.draw.arc(surface, color, rect, 3.4, 5.95, 1)

    def draw(self, graphics, surface, world, wall):
        if isinstance(wall, Pylon):
            color = (255, 164, 128) if wall.polarity > 0 else (123, 205, 245)
            pygame.draw.circle(surface, (28, 33, 42), wall.center, 21)
            image = graphics.render_sprite(self.sprite(world), 37, color)
            surface.blit(image, image.get_rect(center=wall.center))
            pygame.draw.circle(surface, color, wall.center, 21, 2)
            pygame.draw.line(surface, color, wall.center+Vec(-6, 0), wall.center+Vec(6, 0), 2)
            if wall.polarity > 0: pygame.draw.line(surface, color, wall.center+Vec(0, -6), wall.center+Vec(0, 6), 2)
        else:
            pygame.draw.rect(surface, (35, 43, 54), wall.rect, border_radius=4)
            pygame.draw.line(surface, (135, 174, 183), wall.rect.topleft, wall.rect.topright, 2)
            pygame.draw.line(surface, (83, 104, 121), wall.rect.bottomleft, wall.rect.bottomright, 2)
            for x in range(wall.rect.left+8, wall.rect.right, 15):
                pygame.draw.line(surface, (65, 81, 95), (x, wall.rect.top+3), (x, wall.rect.bottom-3), 1)
