"""Signal Runner — complete, independently playable Pak behaviors."""
import math
import pygame
from ..model import Vec, WIDTH, HEIGHT, Cover, Beam, normalized, unit, circle_rect
from .model import Pak

def move(world, dt, control, jump, special):
    p = world.player
    direction = Vec(control.x, control.y)
    if direction.length_squared() > 1:
        direction.normalize_ip()
    p.vel = direction * (640 if p.phase_timer > 0 else 220)
    if direction.length_squared():
        p.angle = math.atan2(direction.y, direction.x)
    world.move_body(p, p.vel * dt, 12)

def fire(world, direction):
    world.spawn_shot(direction, 'pulse', damage=16, speed=520)

def advance_enemy(world, enemy, dt):
    toward = normalized(world.player.pos - enemy.pos)
    speed = (45 + world.wave * 3) * world.factor
    enemy.vel = toward.rotate_rad(math.sin(enemy.age * 2 + enemy.id) * .35) * speed * 1.2
    world.move_body(enemy, enemy.vel * dt, enemy.radius)

def make_arena():
    layout = [(180, 100, 38, 110), (180, 310, 38, 70), (440, 180, 80, 38), (740, 90, 38, 90), (740, 280, 38, 110)]
    return [Cover(pygame.Rect(*rect), platform=False) for rect in layout]

PAK = Pak("signal_runner", "Signal Runner", "PRECISION / SWARM", (71, 224, 244),
          "runner", "pulse", "swarm", "servers",
          "Arrows / WASD: strafe", "X: dash through danger",
          "Outrun the swarm. Thread the signal rooms with rapid pulse fire.", 0, move=move, fire=fire, advance_enemy=advance_enemy, make_arena=make_arena, cooldown=0.14, splits=0)
