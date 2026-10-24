"""Phase Garden — complete, independently playable Pak behaviors."""
import math
import pygame
from ..model import Vec, WIDTH, HEIGHT, Cover, Beam, normalized, unit, circle_rect
from .model import Pak

def move(world, dt, control, jump, special):
    p = world.player
    direction = Vec(control.x, control.y)
    if direction.length_squared() > 1:
        direction.normalize_ip()
    if direction.length_squared():
        p.angle = math.atan2(direction.y, direction.x)
    if special:
        p.pos = world.safe_position(p.pos + unit(p.angle) * 160, 12)
        world.burst(p.pos, world.pak("pilot").color, 16)
    p.vel = direction * 235
    # Distinct step-dash rhythm, expressed in simulation seconds.
    if world.time % .20 < .13:
        world.move_body(p, p.vel * (dt * 1.54), 12)

def fire(world, direction):
    remaining = [enemy for enemy in world.enemies if enemy.health > 0]
    start = world.player.pos.copy()
    for _ in range(4):
        if not remaining:
            break
        target = min(remaining, key=lambda enemy: enemy.pos.distance_squared_to(start))
        world.beams.append(Beam(start, target.pos.copy()))
        world.damage_enemy(target, 26)
        start = target.pos.copy()
        remaining.remove(target)
    for wall in world.cover:
        if circle_rect(world.player.pos, 150, wall.rect):
            wall.health -= 15

def advance_enemy(world, enemy, dt):
    toward = normalized(world.player.pos - enemy.pos)
    speed = (45 + world.wave * 3) * world.factor
    enemy.vel = toward * speed * .65
    world.move_body(enemy, enemy.vel * dt, enemy.radius)
    if enemy.timer <= 0:
        enemy.timer = world.rng.uniform(2.3, 3.8)
        destination = world.player.pos + unit(world.rng.uniform(0, math.tau)) * 175
        world.burst(enemy.pos, world.pak("enemy").color, 5)
        enemy.pos = world.safe_position(destination, enemy.radius, avoid_player=True)
        world.enemy_shot(enemy, toward, 110)

def make_arena():
    layout = [(185, 100, 24, 120), (185, 300, 24, 80), (380, 100, 120, 24), (460, 300, 24, 120), (690, 100, 24, 120), (690, 300, 130, 24)]
    return [Cover(pygame.Rect(*rect), platform=False) for rect in layout]

PAK = Pak("phase_garden", "Phase Garden", "BLINK / CHAIN", (100, 237, 175),
          "phase", "chain", "phantom", "garden",
          "Arrows / WASD: step-dash", "X: blink through cover",
          "Slip through the maze. Chain lightning reveals the hidden garden.", 4, move=move, fire=fire, advance_enemy=advance_enemy, make_arena=make_arena, cooldown=0.58, splits=0)
