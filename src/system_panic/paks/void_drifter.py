"""Void Drifter — complete, independently playable Pak behaviors."""
import math
import pygame
from ..model import Vec, WIDTH, HEIGHT, Cover, Beam, normalized, unit, circle_rect
from .model import Pak

def move(world, dt, control, jump, special):
    p = world.player
    direction = Vec(control.x, control.y)
    if direction.length_squared() > 1:
        direction.normalize_ip()
    p.angle += control.x * 3.7 * dt
    p.vel += unit(p.angle) * (-control.y) * 360 * dt
    p.vel *= math.exp(-.22 * dt)
    if special:
        p.vel *= -.25
    if p.vel.length() > 330:
        p.vel.scale_to_length(330)
    world.move_body(p, p.vel * dt, 12, wrap=True)

def fire(world, direction):
    world.spawn_shot(direction, 'lance', damage=42, speed=700, pierce=3)

def advance_enemy(world, enemy, dt):
    toward = normalized(world.player.pos - enemy.pos)
    speed = (45 + world.wave * 3) * world.factor
    enemy.angle += .12 * dt
    enemy.vel = unit(enemy.angle) * speed * .8 + toward * speed * .3
    world.move_body(enemy, enemy.vel * dt, enemy.radius, wrap=True)

def make_arena():
    layout = [(275, 130, 32, 32), (660, 310, 40, 40)]
    return [Cover(pygame.Rect(*rect), platform=False) for rect in layout]

PAK = Pak("void_drifter", "Void Drifter", "INERTIA / FRACTURE", (174, 151, 255),
          "drifter", "lance", "asteroid", "void",
          "Left / right: turn. Up: thrust", "X: brake and reverse thrust",
          "Master momentum. Pierce drifting rocks before they fracture.", 1, move=move, fire=fire, advance_enemy=advance_enemy, make_arena=make_arena, cooldown=0.43, splits=2)
