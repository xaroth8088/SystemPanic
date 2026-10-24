"""Sky Forge — complete, independently playable Pak behaviors."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect

def move(world, dt, control, jump, special):
    p = world.player
    direction = Vec(control.x, control.y)
    if direction.length_squared() > 1:
        direction.normalize_ip()
    if jump and p.jumps < 2:
        p.vel.y = -330
        p.jumps += 1
        p.grounded = False
        world.burst(p.pos + Vec(0, 10), world.pak("pilot").color, 6)
    if special:
        p.vel.y = -450
        p.jumps = 1
    p.vel.x = control.x * 220
    p.vel.y = min(460, p.vel.y + 820 * dt)
    if control.x:
        p.angle = 0 if control.x > 0 else math.pi
    world.move_body(p, p.vel * dt, 12)

def fire(world, direction):
    world.spawn_shot(direction, 'bomb', damage=58, speed=380, radius=7, homing=2.2, blast=85)

def advance_enemy(world, enemy, dt):
    toward = normalized(world.player.pos - enemy.pos)
    speed = (45 + world.wave * 3) * world.factor
    if enemy.timer <= 0:
        enemy.vel = toward * 145
        enemy.timer = 1.4
    enemy.vel *= math.exp(-1.8 * dt)
    world.move_body(enemy, enemy.vel * dt, enemy.radius)

def make_arena():
    layout = [(100, 365, 180, 18), (360, 290, 180, 18), (640, 365, 190, 18), (150, 185, 180, 18), (620, 185, 180, 18)]
    return [Cover(pygame.Rect(*rect), platform=True) for rect in layout]

def draw_arena(surface):
    pygame.draw.line(surface, (90, 43, 53), (0, HEIGHT - 3), (WIDTH, HEIGHT - 3), 3)

def demo_controls(world):
    p = world.player
    target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
    delta = target.pos - p.pos
    vector = normalized(delta)
    special = int(world.time * 3) % 11 == 0
    return Controls(vector.x if delta.length() > 180 else -vector.x, -1 if world.time % 1.2 < .15 else 0, True, special)
