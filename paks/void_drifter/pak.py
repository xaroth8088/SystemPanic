"""Void Drifter — complete, independently playable Pak behaviors."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect

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

def draw_arena(surface):
    for i in range(95):
        x, y = (i * 137 + 17) % WIDTH, (i * 79 + 13) % HEIGHT
        pygame.draw.circle(surface, (55 + i % 80, 65 + i % 80, 95 + i % 90), (x, y), 1)

def demo_controls(world):
    p = world.player
    target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
    delta = target.pos - p.pos
    vector = normalized(delta)
    special = int(world.time * 3) % 11 == 0
    angle = math.atan2(delta.y, delta.x)
    diff = (angle - p.angle + math.pi) % math.tau - math.pi
    return Controls(max(-1, min(1, diff * 2)), -1 if delta.length() > 180 else .3, True, special)
