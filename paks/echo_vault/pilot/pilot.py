"""Pak-owned movement, recovery and ordinary-input demonstration policy."""
import math
from collections import deque
import pygame
from system_panic.model import Pilot, Vec, Controls, WIDTH, HEIGHT, normalized, unit
from system_panic.pak_api import PilotBase


class PilotController(PilotBase):
    controls = 'Arrows / WASD: move and record your route'
    special = 'X: rewind two seconds of position'

    def init(self):
        self.art = self.load_asset('pilot_sheet.png')
        self.sound = self.load_asset('special.ogg')
        self.cooldown = 0.
        self.ability = 0.
        self.previous_special = False
        self.history = deque()
        self.heading = Vec(1, 0)

    def create(self, world, position):
        return Pilot(pos=Vec(position), health=100, max_health=100, radius=11)

    def sprite(self,world,entity=None):
        actor=entity if entity is not None else (world.player if world is not None else None)
        angle=actor.angle if actor is not None else 0.
        facing=int((angle+math.tau/16)%math.tau/(math.tau/8))
        phase=int((world.time if world is not None else 0)*8)%4
        return self.art.frame(phase*8+facing,columns=8,rows=4)

    def sprite_angle(self,world,entity):return 0.

    def sprite_flip_x(self,world,entity):return False



    def on_level_start(self, world):
        self.history.clear()
        world.player.invulnerable = max(world.player.invulnerable, 1.4)
        if world.wave > 1:
            world.player.health = min(world.player.max_health, world.player.health + 9)

    def on_shuffle(self, world, changed):
        self.history.clear()
        world.player.invulnerable = max(world.player.invulnerable, 1.2)

    def take_damage(self, world, damage):
        applied = world.apply_damage(world.player, damage)
        if applied:
            world.player.invulnerable = .8
            world.shake = 4
            world.events.append('hurt')
            world.burst(world.player.pos, (255, 120, 150), 10)
        return applied

    def on_death(self, world):
        world.burst(world.player.pos, world.pak('pilot').color, 35)

    def update(self, world, dt, control):
        self.cooldown = max(0., self.cooldown - dt)
        self.ability = max(0., self.ability - dt)
        pressed = control.special and not self.previous_special and self.cooldown <= 0
        self.previous_special = control.special
        direction = Vec(control.x, control.y)
        if direction.length_squared() > 1:
            direction.normalize_ip()
        if direction.length_squared() > .01:
            self.heading = direction.normalize()
            world.player.angle = math.atan2(self.heading.y, self.heading.x)
        if pressed:
            self.sound.play(volume=.45)
        self.move(world, dt, direction, pressed)

    def demo_controls(self, world):
        if not world.enemies:
            return Controls()
        p = world.player
        target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
        delta = target.pos - p.pos
        distance = delta.length()
        toward = normalized(delta)
        tangent = Vec(-toward.y, toward.x)
        direction = toward if distance > 205 else tangent * .8 - toward * .45
        # QA uses only public projectile threat/position data and ordinary
        # inputs, demonstrating the routes/rewinds a human can choose.
        danger=False
        for shot in world.projectiles:
            if not shot.alive or not shot.is_threat_to(world,p):continue
            delta=shot.pos-p.pos
            relative=shot.vel-p.vel
            t=max(0.,min(.55,-delta.dot(relative)/max(.01,relative.length_squared())))
            predicted=shot.pos+shot.vel*t
            if predicted.distance_to(p.pos)<shot.radius+55:
                direction+=normalized(p.pos-predicted)*1.8
                danger=True
        if p.pos.x < 65: direction.x = 1
        if p.pos.x > WIDTH - 65: direction.x = -1
        if p.pos.y < 65: direction.y = 1
        if p.pos.y > HEIGHT - 65: direction.y = -1
        fire = True
        # QA selects the same eight digital directions as keyboard / D-pad.
        direction = Vec((direction.x > .2) - (direction.x < -.2),
                        (direction.y > .2) - (direction.y < -.2))
        return Controls(direction.x, direction.y, fire, danger and self.cooldown<=0)

    def move(self, world, dt, direction, pressed):
        p = world.player
        self.history.append((world.time, p.pos.copy()))
        while self.history and world.time - self.history[0][0] > 2.:
            self.history.popleft()
        if pressed and self.history:
            self.cooldown, self.ability = 4.5, .5
            previous = p.pos.copy()
            p.pos = world.safe_position(self.history[0][1], p.radius)
            self.history.clear()
            p.invulnerable = max(p.invulnerable, .6)
            world.burst(previous, (100, 200, 255), 15)
        p.vel = direction * (270 if self.ability > 0 else 210)
        world.move_body(p, p.vel * dt, p.radius)

    def status(self, world):
        return f'RECORDED {min(2., len(self.history) / 120):.1f}s  |  REWIND {self.cooldown:.1f}s'
