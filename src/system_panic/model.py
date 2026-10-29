"""Engine-owned state. Pak-specific state is never transferred across behaviors."""
from dataclasses import dataclass, field
import math

import pygame
from pygame.math import Vector2

Vec = Vector2
WIDTH, HEIGHT = 960, 480
FIXED_DT = 1 / 120


@dataclass
class Controls:
    x: float = 0
    y: float = 0
    fire: bool = False
    special: bool = False


@dataclass
class Body:
    """Shared physical/damage state; gameplay-specific state belongs to a Pak."""
    pos: Vec = field(default_factory=Vec)
    vel: Vec = field(default_factory=Vec)
    angle: float = 0.
    radius: float = 1.
    health: float = 1.
    max_health: float = 1.
    invulnerable: float = 0.

    def overlaps_circle(self, position, radius):
        """Neutral default body shape; Pak subclasses may supply other shapes."""
        return self.pos.distance_squared_to(position)<(self.radius+radius)**2


@dataclass
class Pilot(Body):
    pass


@dataclass
class Enemy(Body):
    id: int = 0


@dataclass
class Cover:
    rect: pygame.Rect
    health: float
    max_health: float

    def overlaps_circle(self, position, radius):
        return circle_rect(position, radius, self.rect)

    def navigation_key(self):
        """Optional immutable collision snapshot for local navigation caches.

        Equal keys promise identical circle overlaps for a given radius and
        conservative rect bounds. Custom shapes opt in with all shape state;
        None keeps arbitrary queries on the body-local, shape-aware path.
        Body filtering is always evaluated separately by the caller.
        """
        if getattr(self.overlaps_circle, "__func__", None) is Cover.overlaps_circle:
            return (Cover, tuple(self.rect))
        return None

    def overlaps_segment(self, start, end):
        return bool(self.rect.clipline(start, end))

    def blocks_body(self, body):
        return True

    def blocks_projectile(self, projectile):
        return True

    def on_contact(self, world, body, normal):
        """Return True to consume a handled response; otherwise expose its normal."""

    def damage(self, world, amount):
        return world.component("obstacles").take_damage(world, self, amount)

    def draw(self, graphics, surface, world):
        world.component("obstacles").draw(graphics, surface, world, self)


@dataclass(frozen=True)
class Motion:
    """Collision normals, with no automatic jump/velocity/bounce policy."""
    normals: tuple[Vec, ...] = ()

    @property
    def blocked_y(self):
        return any(normal.y for normal in self.normals)

    @property
    def landed(self):
        return any(normal.y < 0 for normal in self.normals)


@dataclass
class Particle:
    pos: Vec
    vel: Vec
    color: tuple[int, int, int]
    life: float
    maximum: float
    size: float = 3


def unit(angle: float) -> Vec:
    return Vec(math.cos(angle), math.sin(angle))


def normalized(vector: Vec, fallback: Vec | None = None) -> Vec:
    return vector.normalize() if vector.length_squared() > .00001 else Vec(fallback or (1, 0))


def circle_rect(pos: Vec, radius: float, rect: pygame.Rect) -> bool:
    nearest = Vec(max(rect.left, min(pos.x, rect.right)), max(rect.top, min(pos.y, rect.bottom)))
    return pos.distance_squared_to(nearest) < radius * radius
