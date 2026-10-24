"""Engine-owned state. Pak-specific state is never transferred across behaviors."""
from dataclasses import dataclass, field
import math

import pygame

Vec = pygame.Vector2
WIDTH, HEIGHT = 960, 480
FIXED_DT = 1 / 120


@dataclass
class Controls:
    x: float = 0
    y: float = 0
    fire: bool = False
    special: bool = False


@dataclass
class Pilot:
    pos: Vec = field(default_factory=lambda: Vec(WIDTH / 2, HEIGHT / 2))
    vel: Vec = field(default_factory=Vec)
    angle: float = -math.pi / 2
    health: float = 100
    invulnerable: float = 1.5
    fire_timer: float = 0
    special_timer: float = 0
    grounded: bool = False
    jumps: int = 0
    phase_timer: float = 0
    orbit_radius: float = 170
    orbit_direction: int = 1


@dataclass
class Enemy:
    id: int
    pos: Vec
    family: str
    health: float
    max_health: float
    radius: float = 14
    vel: Vec = field(default_factory=Vec)
    timer: float = 1
    age: float = 0
    angle: float = 0
    size: int = 0
    elite: bool = False


@dataclass
class Projectile:
    pos: Vec
    vel: Vec
    kind: str
    damage: float
    life: float
    friendly: bool = True
    radius: float = 4
    pierce: int = 0
    bounce: int = 0
    age: float = 0
    hit_ids: set[int] = field(default_factory=set)
    homing: float = 0.
    blast: float = 0.
    return_after: float = -1.


@dataclass
class Cover:
    rect: pygame.Rect
    health: float = 36
    platform: bool = False


@dataclass
class Particle:
    pos: Vec
    vel: Vec
    color: tuple[int, int, int]
    life: float
    maximum: float
    size: float = 3


@dataclass
class Beam:
    start: Vec
    end: Vec
    life: float = .16


def unit(angle: float) -> Vec:
    return Vec(math.cos(angle), math.sin(angle))


def normalized(vector: Vec, fallback: Vec | None = None) -> Vec:
    return vector.normalize() if vector.length_squared() > .00001 else Vec(fallback or (1, 0))


def circle_rect(pos: Vec, radius: float, rect: pygame.Rect) -> bool:
    nearest = Vec(max(rect.left, min(pos.x, rect.right)), max(rect.top, min(pos.y, rect.bottom)))
    return pos.distance_squared_to(nearest) < radius * radius
