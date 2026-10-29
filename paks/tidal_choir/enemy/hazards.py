"""Active ink clouds and jet wakes; delayed damage remains invisible."""
from functools import lru_cache
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT
from system_panic.pak_api import ProjectileBase


@lru_cache(maxsize=16)
def ink_cloud(radius):
    """Reuse the filled stain; the cached image is never modified by drawing."""
    surface = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
    center = Vec(radius + 1, radius + 1)
    for r in range(radius, 0, -1):
        depth = 1 - r / radius
        color = (int(83 - 61 * depth), int(58 - 43 * depth), int(126 - 81 * depth), int(95 + 140 * depth))
        pygame.draw.circle(surface, color, center, r)
    for i in range(9):
        angle = i * 2.4
        point = center + Vec(math.cos(angle), math.sin(angle)) * radius * (.48 + .12 * (i % 2))
        pygame.draw.circle(surface, (47, 26, 78, 215), point, max(2, int(radius * .28)))
        pygame.draw.arc(surface, (130, 102, 181, 160),
                        (point.x - radius * .28, point.y - radius * .28, radius * .56, radius * .56),
                        angle, angle + 2.1, 2)
    return surface


def draw_charge_wake(surface, enemy, *, inky, reduced_motion):
    """Follow a charge already in progress, never preview its target or path."""
    if enemy.state != 'charge' or enemy.vel.length_squared() < 1:
        return
    heading = enemy.vel.normalize()
    side = Vec(-heading.y, heading.x)
    rear = enemy.pos - heading * enemy.radius
    phase = 0. if reduced_motion else (enemy.age * 12) % 1
    for i in range(3):
        spread = (i - 1) * 6
        start = rear + side * spread
        end = rear - heading * (30 + 8 * (i % 2)) + side * spread * 2
        pygame.draw.line(surface, (116, 199, 209), start, end, 2)
        if inky:
            tip = rear - heading * (9 + i * 15 + phase * 7)
            back = tip - heading * 14
            points = [tip, back + side * 5, back - heading * 3, back - side * 5]
            pygame.draw.polygon(surface, (60, 35, 94), points)
            pygame.draw.lines(surface, (149, 112, 193), False, points[:3], 1)




class Bolt(ProjectileBase):
    def __init__(self, position, velocity, damage, radius=4):
        super().__init__(position,velocity,radius)
        self.damage,self.age=damage,0.

    def update(self, world, dt):
        self.age+=dt
        previous=self.pos.copy()
        self.pos+=self.vel*dt
        if self.age>4 or not(-8<self.pos.x<WIDTH+8 and -8<self.pos.y<HEIGHT+8):self.alive=False
        for wall in world.geometry:
            if wall.health>0 and wall.blocks_projectile(self) and wall.overlaps_segment(previous,self.pos):
                world.hit_cover(wall,self.damage)
                self.alive=False
                return
        if self.pos.distance_to(world.player.pos)<world.player.radius+self.radius:
            world.hit_player(self.damage)
            self.alive=False

    def is_threat_to(self, world, body):
        return body is world.player

    def draw(self, graphics, surface, world):
        pygame.draw.line(surface,(125,65,95),self.pos-self.vel*.04,self.pos,3)
        pygame.draw.circle(surface,(255,140,165),self.pos,self.radius)
        pygame.draw.circle(surface,(255,235,215),self.pos,2)


class Zone(ProjectileBase):
    def __init__(self, position, radius, delay, damage, duration=.35):
        super().__init__(position,Vec(),radius)
        self.delay,self.damage,self.duration,self.age=delay,damage,duration,0.

    def update(self, world, dt):
        self.age+=dt
        if self.age>=self.delay:
            if self.pos.distance_to(world.player.pos)<self.radius+world.player.radius:
                world.hit_player(self.damage)
            if self.age>self.delay+self.duration:self.alive=False

    def is_threat_to(self, world, body):
        return body is world.player

    def draw(self, graphics, surface, world):
        if not self.alive or self.age < self.delay or self.age > self.delay + self.duration:
            return
        radius = max(1, int(self.radius))
        cloud = ink_cloud(radius)
        surface.blit(cloud, cloud.get_rect(center=self.pos))
        # Inky lobes and drifting flecks describe a lingering cloud, not a target marker.
        progress = .4 if world.prefs.reduced_motion else (self.age - self.delay) / self.duration
        for i in range(8):
            angle = i * 2.4 + progress * .65
            ring = (.30 + .43 * progress) if i % 2 else (.57 + .14 * math.sin(progress * math.tau))
            point = self.pos + Vec(math.cos(angle), math.sin(angle)) * self.radius * ring
            size = max(2, int(self.radius * (.09 if i % 2 else .15)))
            pygame.draw.circle(surface, (70, 40, 105), point, size)
            pygame.draw.arc(surface, (166, 124, 212), (point.x - size, point.y - size, size * 2, size * 2),
                            angle, angle + 2., 2)
