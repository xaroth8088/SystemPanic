"""Sky Forge — complete, independently playable Pak behaviors."""
import math
import pygame
from ..model import Vec, WIDTH, HEIGHT, Cover, Beam, normalized, unit, circle_rect
from .model import Pak

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

PAK = Pak("sky_forge", "Sky Forge", "GRAVITY / BLAST", (255, 119, 137),
          "jumper", "bomb", "hopper", "forge",
          "Left / right: run. Up: double jump", "X: rising forge leap",
          "Leap between forge decks. Explosive arcs scatter the crawlers.", 3, move=move, fire=fire, advance_enemy=advance_enemy, make_arena=make_arena, cooldown=0.6, splits=0)
