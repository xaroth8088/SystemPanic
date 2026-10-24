"""Iron Circuit — complete, independently playable Pak behaviors."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect

def move(world, dt, control, jump, special):
    p = world.player
    direction = Vec(control.x, control.y)
    if direction.length_squared() > 1:
        direction.normalize_ip()
    p.angle += control.x * 2.9 * dt
    speed = 190 - control.y * 75 + (190 if p.phase_timer > 0 else 0)
    p.vel = unit(p.angle) * speed
    old = p.pos.copy()
    world.move_body(p, p.vel * dt, 12)
    if p.pos.distance_to(old) < speed * dt * .35:
        p.angle += math.pi * .7

def fire(world, direction):
    for offset in (-.20, 0, .20):
        world.spawn_shot(direction.rotate_rad(offset), 'scatter', damage=19, speed=440, bounce=4)

def advance_enemy(world, enemy, dt):
    toward = normalized(world.player.pos - enemy.pos)
    speed = (45 + world.wave * 3) * world.factor
    enemy.angle = math.atan2(toward.y, toward.x)
    if enemy.timer <= 0:
        enemy.timer = max(.8, 2.8 / world.factor - world.wave * .08)
        world.enemy_shot(enemy, toward, 130 + world.wave * 5)
        if enemy.elite:
            world.enemy_shot(enemy, toward.rotate_rad(.3), 140)
            world.enemy_shot(enemy, toward.rotate_rad(-.3), 140)

def make_arena():
    layout = [(240, 130, 110, 42), (240, 308, 110, 42), (610, 130, 110, 42), (610, 308, 110, 42), (456, 216, 48, 48)]
    return [Cover(pygame.Rect(*rect), platform=False) for rect in layout]

def draw_arena(surface):
    pygame.draw.rect(surface, (54, 42, 31), (75, 55, 810, 370), 2, border_radius=80)
    pygame.draw.rect(surface, (54, 42, 31), (120, 100, 720, 280), 1, border_radius=60)

def demo_controls(world):
    p = world.player
    target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
    delta = target.pos - p.pos
    vector = normalized(delta)
    special = int(world.time * 3) % 11 == 0
    return Controls(math.sin(world.time * .7) * .7, -.3, True, special)
