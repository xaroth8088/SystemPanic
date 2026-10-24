"""Orbit Keeper — complete, independently playable Pak behaviors."""
import math
import pygame
from ..model import Vec, WIDTH, HEIGHT, Cover, Beam, normalized, unit, circle_rect
from .model import Pak

def move(world, dt, control, jump, special):
    p = world.player
    direction = Vec(control.x, control.y)
    if direction.length_squared() > 1:
        direction.normalize_ip()
    if special:
        p.orbit_direction *= -1
    p.angle += (control.x * 2.2 if control.x else .65 * p.orbit_direction) * dt
    p.orbit_radius = max(70, min(215, p.orbit_radius + control.y * 150 * dt))
    target = Vec(WIDTH / 2, HEIGHT / 2) + unit(p.angle) * p.orbit_radius
    p.vel = (target - p.pos) * 12
    world.move_body(p, p.vel * dt, 12)

def fire(world, direction):
    world.spawn_shot(direction, 'glaive', damage=28, speed=430, radius=7, pierce=6, return_after=.55)

def advance_enemy(world, enemy, dt):
    toward = normalized(world.player.pos - enemy.pos)
    speed = (45 + world.wave * 3) * world.factor
    center = Vec(WIDTH / 2, HEIGHT / 2)
    enemy.angle += (.40 + world.wave * .02) * dt * (-1 if enemy.id % 2 else 1)
    radius = 90 + (enemy.id % 4) * 42
    target = center + unit(enemy.angle) * radius
    enemy.vel = (target - enemy.pos) * 1.5
    world.move_body(enemy, enemy.vel * dt, enemy.radius)
    if enemy.timer <= 0:
        enemy.timer = 2.7 / world.factor
        world.enemy_shot(enemy, toward, 120)

def make_arena():
    layout = [(440, 200, 80, 80), (130, 100, 32, 32), (798, 100, 32, 32), (130, 348, 32, 32), (798, 348, 32, 32)]
    return [Cover(pygame.Rect(*rect), platform=False) for rect in layout]

PAK = Pak("orbit_keeper", "Orbit Keeper", "ORBIT / RETURN", (242, 225, 112),
          "orbiter", "glaive", "sentinel", "orbit",
          "Left / right: orbit. Up / down: radius", "X: reverse orbit and shield",
          "Hold the orbit. Returning glaives cut through circling sentinels.", 5, move=move, fire=fire, advance_enemy=advance_enemy, make_arena=make_arena, cooldown=0.48, splits=0)
