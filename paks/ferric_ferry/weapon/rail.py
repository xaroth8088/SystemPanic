"""Fixed physical terminals and rail conduction; no orbit, seeking or ammo pool."""
import math
import pygame
from system_panic.model import Body, Cover, Vec, normalized
from system_panic.pak_api import ProjectileBase


def closest_point(point, start, end):
    delta = end-start
    t = max(0., min(1., (Vec(point)-start).dot(delta)/max(.0001, delta.length_squared())))
    return start+delta*t


def overlaps_path(body, start, end, radius):
    query = body.overlaps_circle
    if getattr(query, '__func__', None) is Body.overlaps_circle:
        # The inherited public circle shape has an exact nearest-point query.
        return query(closest_point(body.pos, start, end), radius)
    # Custom footprints need their actual query along the sweep; their nominal
    # center/radius or broad bounds are not a substitute for that contract.
    steps = max(1, math.ceil(start.distance_to(end)/max(1., min(4., radius*.5))))
    return any(query(start.lerp(end, index/steps), radius) for index in range(steps+1))


def conducting_path(world, start, end, projectile, radius=0.):
    """Clip to the first real projectile-blocking shape using its public query."""
    start, end = Vec(start), Vec(end)
    walls = [wall for wall in world.geometry if wall.health > 0 and wall.blocks_projectile(projectile)]
    if radius > 0:
        # Metadata is conservative broad phase only; every actual collision
        # still uses the shape's public circle query, including grazing cover.
        padding = math.ceil(radius*2+2)
        walls = [wall for wall in walls if wall.rect.inflate(padding, padding).clipline(start, end)
                 or wall.overlaps_circle(start, radius)]
        if not walls: return start, end, None
        previous = start.copy()
        steps = max(1, math.ceil(start.distance_to(end)/max(1., min(4., radius))))
        for index in range(steps+1):
            proposed = start.lerp(end, index/steps)
            wall = next((wall for wall in walls if wall.overlaps_circle(proposed, radius)), None)
            if wall is not None:
                low, high = 0., 1.
                for _ in range(12):
                    middle = (low+high)/2
                    if wall.overlaps_circle(previous.lerp(proposed, middle), radius): high = middle
                    else: low = middle
                return start, previous.lerp(proposed, low), wall
            previous = proposed
        return start, end, None
    blocked = [wall for wall in walls if wall.overlaps_segment(start, end)]
    if not blocked: return start, end, None
    low, high = 0., 1.
    for _ in range(14):
        middle = (low+high)/2
        point = start.lerp(end, middle)
        if any(wall.overlaps_segment(start, point) for wall in blocked): high = middle
        else: low = middle
    point = start.lerp(end, low)
    probe = start.lerp(end, high)
    wall = next(wall for wall in blocked if wall.overlaps_segment(start, probe))
    return start, point, wall


class Terminal(Cover):
    def __init__(self, position, art, color):
        self.position = Vec(position)
        self.art, self.color = art, color
        super().__init__(pygame.Rect(round(position.x)-13, round(position.y)-13, 26, 26), 100, 100)
    def blocks_body(self, body): return False
    def blocks_projectile(self, projectile): return False
    def damage(self, world, amount): return 0.
    def draw(self, graphics, surface, world):
        pygame.draw.circle(surface, (33, 36, 46), self.position, 12)
        pygame.draw.line(surface, self.color, self.position+Vec(-8, 9), self.position+Vec(8, 9), 2)
        image = graphics.render_sprite(self.art.frame(0, columns=4), 26, self.color)
        surface.blit(image, image.get_rect(center=self.position))


class Conduit(Cover):
    def __init__(self, start, end, color):
        self.start, self.end = Vec(start), Vec(end)
        self.live_end = Vec(end)
        self.color, self.powered, self.strength = color, False, 0.
        super().__init__(pygame.Rect(math.floor(min(start.x, end.x))-5, math.floor(min(start.y, end.y))-5,
                                    max(10, math.ceil(abs(end.x-start.x))+10), max(10, math.ceil(abs(end.y-start.y))+10)), 100, 100)
    def blocks_body(self, body): return False
    def blocks_projectile(self, projectile): return False
    def damage(self, world, amount): return 0.
    def draw(self, graphics, surface, world):
        # This is a planted copper conductor, not an aim line.
        pygame.draw.line(surface, (67, 56, 53), self.start, self.end, 3)
        pygame.draw.line(surface, (122, 89, 66), self.start, self.end, 1)
        if self.powered:
            color = (151+int(65*self.strength), 210, 252)
            pygame.draw.line(surface, (39, 81, 105), self.start, self.live_end, 7)
            pygame.draw.line(surface, color, self.start, self.live_end, 2)
            delta = self.live_end-self.start
            if delta.length_squared():
                for index in range(7):
                    t = (index/7+world.time*(.5+self.strength*.6))%1
                    point = self.start+delta*t
                    pygame.draw.circle(surface, color, point, 2)


class Armature(ProjectileBase):
    def __init__(self, start, end, charge, upgrades, art, color):
        self.start, self.end = Vec(start), Vec(end)
        self.direction = normalized(self.end-self.start)
        self.charge = min(2.4, charge)
        super().__init__(start, self.direction*(600+self.charge*90), 10+min(7, upgrades*.6))
        self.art, self.color = art, color
        self.damage = 46+46*self.charge+6*upgrades
        self.hit = set()
        self.travel = self.age = 0.
        self.speed = self.vel.length()

    def update(self, world, dt):
        if not self.alive: return
        self.age += dt
        if self.age > 2.8:
            self.alive = False
            return
        previous = self.pos.copy()
        total = self.start.distance_to(self.end)
        desired = self.start+self.direction*min(total, self.travel+self.speed*dt)
        blocker = None
        steps = max(1, math.ceil(previous.distance_to(desired)/4))
        for index in range(1, steps+1):
            proposed = previous.lerp(desired, index/steps)
            blocker = next((wall for wall in world.geometry if wall.health > 0
                            and wall.blocks_projectile(self) and wall.overlaps_circle(proposed, self.radius)), None)
            if blocker is not None:
                low, high = 0., 1.
                safe = self.pos.copy()
                for _ in range(12):
                    middle = (low+high)/2
                    if blocker.overlaps_circle(safe.lerp(proposed, middle), self.radius): high = middle
                    else: low = middle
                self.pos = safe.lerp(proposed, low)
                break
            self.pos = proposed
        self.travel = self.start.distance_to(self.pos)
        # Rail guidance fixes its direction. External fields may alter public
        # velocity, but cannot detach a mechanical armature from its conductor.
        self.vel = self.direction*self.speed
        for enemy in world.enemies:
            if enemy.health > 0 and enemy.id not in self.hit and overlaps_path(enemy, previous, self.pos, self.radius):
                world.hit_enemy(enemy, self.damage)
                world.move_body(enemy, self.direction*(20+12*self.charge), enemy.radius)
                enemy.vel += self.direction*90
                self.hit.add(enemy.id)
                world.burst(enemy.pos, self.color, 5)
        if blocker is not None:
            world.hit_cover(blocker, self.damage*.65)
            world.burst(self.pos, self.color, 9)
            self.alive = False
        elif self.travel >= total-.01:
            self.alive = False
            world.burst(self.pos, self.color, 7)

    def draw(self, graphics, surface, world):
        side = Vec(-self.direction.y, self.direction.x)
        pygame.draw.line(surface, (38, 80, 105), self.pos-self.direction*25, self.pos, 7)
        pygame.draw.line(surface, (210, 235, 255), self.pos-side*(self.radius+4), self.pos+side*(self.radius+4), 4)
        image = graphics.render_sprite(self.art.frame(2+int(self.age*14)%2, columns=4), 31, self.color)
        image = pygame.transform.rotate(image, -math.degrees(math.atan2(self.direction.y, self.direction.x)))
        surface.blit(image, image.get_rect(center=self.pos))
