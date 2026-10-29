"""Physical paper flight, an active unfolding cut and a separate return pass."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, normalized
from system_panic.pak_api import ProjectileBase


class FoldBlade(ProjectileBase):
    def __init__(self, position, direction, charge, upgrades, art, owner):
        super().__init__(position, direction*560, 9)
        self.art, self.owner = art, owner
        self.charge = min(1.1, charge)
        self.damage = 18+24*self.charge+4*upgrades
        self.reach = 30+42*self.charge+min(45, 3*upgrades)
        self.age = 0.
        self.state = 'outbound'
        self.hit = set()
        self.apex = None
        self.unfold_age = 0.

    def unfold(self, world):
        self.state, self.apex = 'unfold', self.pos.copy()
        self.unfold_age = 0.
        self.hit.clear()
        world.burst(self.pos, world.pak('weapon').color, 7)

    def update(self, world, dt):
        if not self.alive: return
        self.age += dt
        if self.age > 3.2:
            self.alive = False
            return
        if self.state == 'outbound' and self.age >= .44+.15*self.charge:
            self.unfold(world)
        if self.state == 'unfold':
            self.unfold_age += dt
            if self.unfold_age >= .12:
                self.state = 'return'
                self.hit.clear()
            else:
                for enemy in world.enemies:
                    if enemy.health > 0 and enemy.id not in self.hit and enemy.pos.distance_to(self.pos) < self.reach+enemy.radius:
                        if not world.segment_blocked(self.pos, enemy.pos, self):
                            world.hit_enemy(enemy, self.damage*.6)
                            self.hit.add(enemy.id)
                return
        if self.state == 'return':
            self.vel = normalized(world.player.pos-self.pos)*650
            if self.pos.distance_to(world.player.pos) < world.player.radius+18:
                self.alive = False
                self.owner.cooldown = max(0., self.owner.cooldown-.25)
                world.burst(self.pos, world.pak('weapon').color, 3)
                return
        distance = self.vel.length()*dt
        steps = max(1, math.ceil(distance/6))
        for _ in range(steps):
            before = self.pos.copy()
            self.pos += self.vel*(dt/steps)
            blocked = next((w for w in world.geometry if w.health > 0 and w.blocks_projectile(self)
                            and w.overlaps_circle(self.pos, self.radius)), None)
            if blocked:
                world.hit_cover(blocked, self.damage*.5)
                self.pos = before
                if self.state == 'outbound':
                    self.unfold(world)
                    break
                # A returning fold flutters down rather than piercing cover.
                self.alive = False
                break
            if self.pos.x < self.radius or self.pos.x > WIDTH-self.radius or self.pos.y < self.radius or self.pos.y > HEIGHT-self.radius:
                self.pos.x = max(self.radius, min(WIDTH-self.radius, self.pos.x))
                self.pos.y = max(self.radius, min(HEIGHT-self.radius, self.pos.y))
                if self.state == 'outbound': self.unfold(world)
                else: self.alive = False
                break
            for enemy in world.enemies:
                if enemy.health > 0 and enemy.id not in self.hit and enemy.overlaps_circle(self.pos, self.radius):
                    world.hit_enemy(enemy, self.damage)
                    self.hit.add(enemy.id)

    def draw(self, graphics, surface, world):
        color = world.pak('weapon').color
        if self.state == 'unfold':
            for turn in range(3):
                direction = Vec(1, 0).rotate(turn*120+self.age*240)
                tangent = Vec(-direction.y, direction.x)
                points = [self.pos+direction*self.reach, self.pos+direction*8+tangent*12, self.pos-tangent*10]
                pygame.draw.polygon(surface, color, points, 2)
        image = graphics.render_sprite(self.art.frame(int(self.age*12)%4, columns=4), 28, color)
        image = pygame.transform.rotate(image, -math.degrees(math.atan2(self.vel.y, self.vel.x)))
        surface.blit(image, image.get_rect(center=self.pos))
