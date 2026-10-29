"""Closed-tail geometry and presentation, owned entirely by this weapon."""
import pygame
from system_panic.pak_api import EffectBase


def intersection(a, b, c, d):
    """Return a crossing on a to b; retracing a straight line encloses nothing."""
    direction, edge = b - a, d - c
    cross = direction.cross(edge)
    if abs(cross) < 1e-8:
        return None
    t, u = (c - a).cross(edge) / cross, (c - a).cross(direction) / cross
    if 1e-7 < t <= 1.0000001 and -1e-7 <= u <= 1.0000001:
        return a + direction * t
    return None


def area(points):
    return abs(sum(a.cross(b) for a, b in zip(points, points[1:] + points[:1]))) / 2


def contains_body(points, body):
    """Require the entire enemy circle to lie inside this simple closed polygon."""
    inside = False
    p = body.pos
    for a, b in zip(points, points[1:] + points[:1]):
        edge = b - a
        length = edge.length_squared()
        closest = a if not length else a + edge * max(0., min(1., (p - a).dot(edge) / length))
        if closest.distance_squared_to(p) < body.radius ** 2:
            return False
        if (a.y > p.y) != (b.y > p.y):
            x = a.x + (p.y - a.y) * (b.x - a.x) / (b.y - a.y)
            if p.x < x:
                inside = not inside
    return inside


class TailImage(EffectBase):
    def __init__(self,art=None):
        self.art=art
        self.points = []
        self.captured = []
        self.flash = 0.
        self.remaining = .05
        self.alive = True

    def update(self, dt):
        self.remaining -= dt
        self.flash = max(0., self.flash - dt)
        self.alive = self.remaining > 0

    def draw(self, graphics, surface, world):
        color = world.pak("weapon").color
        if self.flash and len(self.captured) > 2:
            layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(layer, (*color, int(65 * self.flash / .5)), self.captured)
            surface.blit(layer, (0, 0))
            pygame.draw.lines(surface, color, True, self.captured, 3)
        if len(self.points) > 1:
            pygame.draw.lines(surface, tuple(int(c * .3) for c in color), False, self.points, 7)
            pygame.draw.lines(surface, color, False, self.points, 2)
            pygame.draw.circle(surface, color, self.points[0], 5, 1)
            if self.art is not None:
                image=graphics.render_sprite(self.art.frame(int(world.time*8)%4,columns=4),24,color)
                surface.blit(image,image.get_rect(center=self.points[-1]))
            pass
