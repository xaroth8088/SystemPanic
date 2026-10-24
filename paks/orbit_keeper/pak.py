"""Orbit Keeper — complete, independently playable Pak behaviors."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect

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

def draw_arena(surface):
    for r in (90, 140, 190, 225):
        pygame.draw.circle(surface, (48, 46, 33), (WIDTH // 2, HEIGHT // 2), r, 1)

def prepare_pilot(world):
    offset = world.player.pos - Vec(WIDTH / 2, HEIGHT / 2)
    world.player.angle = math.atan2(offset.y, offset.x)
    world.player.orbit_radius = max(80, min(215, offset.length()))

def demo_controls(world):
    p = world.player
    target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
    delta = target.pos - p.pos
    vector = normalized(delta)
    special = int(world.time * 3) % 11 == 0
    steering = .7
    threats = [enemy.pos + enemy.vel * .25 for enemy in world.enemies if enemy.health > 0]
    threats += [shot.pos + shot.vel * .25 for shot in world.projectiles if not shot.friendly]
    if threats and min(p.pos.distance_to(pos) for pos in threats) < 90:
        steering = max((-.7, .7), key=lambda x: min(
            (Vec(WIDTH / 2, HEIGHT / 2) + unit(p.angle + x * 2.2 * .35) * p.orbit_radius).distance_to(pos)
            for pos in threats))
    return Controls(steering, math.sin(world.time * .7) * .4, True, special)
