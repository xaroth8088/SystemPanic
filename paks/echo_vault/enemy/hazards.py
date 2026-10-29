"""Only active Pak-owned hazards are drawn; delayed damage timing stays local."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT
from system_panic.pak_api import ProjectileBase, EffectBase




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
    def __init__(self, position, radius, delay, damage, duration=.35, source=None):
        super().__init__(position,Vec(),radius)
        self.delay,self.damage,self.duration,self.age=delay,damage,duration,0.
        self.source = Vec(source) if source is not None else None

    def update(self, world, dt):
        self.age+=dt
        if self.age>=self.delay:
            if self.pos.distance_to(world.player.pos)<self.radius+world.player.radius:
                world.hit_player(self.damage)
            if self.age>self.delay+self.duration:self.alive=False

    def is_threat_to(self, world, body):
        return body is world.player

    def draw(self, graphics, surface, world):
        if self.age<self.delay:return
        progress = min(1., (self.age - self.delay) / self.duration)
        reduced = world.prefs.reduced_motion
        # The filled footprint exists only while this burst can hurt the pilot.
        size = int(self.radius * 2 + 10)
        glow = pygame.Surface((size, size), pygame.SRCALPHA)
        center = Vec(size / 2, size / 2)
        pygame.draw.circle(glow, (140, 72, 210, 65), center, int(self.radius))
        surface.blit(glow, self.pos - center)
        pygame.draw.circle(surface, (205, 148, 255), self.pos, int(self.radius), 2)
        radius = self.radius * (.7 if reduced else .18 + .82 * progress)
        pygame.draw.circle(surface, (184, 230, 255), self.pos, max(2, int(radius)), 2)
        if self.source is not None and progress < .34:
            pygame.draw.line(surface, (119, 86, 165), self.source, self.pos, 2)
            pygame.draw.circle(surface, (205, 148, 255), self.source, 7, 2)
        # Broken clock spokes converge on a bright impact, replacing the plain red X.
        for i in range(8):
            angle = i * math.tau / 8
            ray = Vec(math.cos(angle), math.sin(angle))
            inner = self.pos + ray * (7 if reduced else 5 + 14 * progress)
            outer = self.pos + ray * (self.radius * .83)
            pygame.draw.line(surface, (174, 119, 227), inner, outer, 2)
        pygame.draw.circle(surface, (230, 242, 255), self.pos, 4 if reduced else max(2, int(8 * (1 - progress))))


class BlinkEcho(EffectBase):
    """Departure/arrival residue after a flank blink, never an attack warning."""
    def __init__(self, departure, arrival, sprite):
        self.departure, self.arrival = Vec(departure), Vec(arrival)
        self.sprite, self.age, self.alive = sprite, 0., True

    def update(self, dt):
        self.age += dt
        self.alive = self.age < .28

    def draw(self, graphics, surface, world):
        fade = max(0., 1 - self.age / .28)
        image = graphics.render_sprite(self.sprite, 34, (179, 217, 255)).copy()
        image.set_alpha(int(140 * fade))
        surface.blit(image, image.get_rect(center=self.departure))
        if not world.prefs.reduced_motion:
            pygame.draw.line(surface, (int(83 * fade), int(118 * fade), int(162 * fade)), self.departure, self.arrival, 1)
        pygame.draw.circle(surface, (int(160 * fade), int(211 * fade), int(245 * fade)), self.arrival, 19, 2)
