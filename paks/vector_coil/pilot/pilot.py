"""Vector Coil: raw-input movement and abilities belong to this component."""
import math
import pygame
from system_panic.model import Pilot, Vec, Controls, WIDTH, HEIGHT, unit, normalized, circle_rect
from system_panic.pak_api import PilotBase


class VectorCoilPilot(PilotBase):
    controls = 'Arrows / WASD: right-angle turns. Hold FIRE: draw capture tail'
    special = 'X: reverse the trail and shield'

    def init(self):
        self.art = self.load_asset("pilot_sheet.png")
        self.sound = self.load_asset("special.ogg")
        self._previous_special = False
        self._special_remaining = 0.
        self._direction = Vec(1,0)
        self._turn_lock = 0.
        self._demo_corner = -1
        self._demo_entry = None

    def sprite(self, world, entity=None):
        return self.art

    def create(self, world, position):
        return Pilot(pos=Vec(position), health=100, max_health=100, radius=11, angle=-math.pi / 2)

    def on_level_start(self, world):
        if world.wave > 1:
            world.player.health = min(world.player.max_health, world.player.health + 15)
        world.player.invulnerable = max(world.player.invulnerable, 2.)

    def on_shuffle(self, world, changed):
        world.player.invulnerable = max(world.player.invulnerable, 1.5)

    def take_damage(self, world, damage):
        applied = world.apply_damage(world.player, damage)
        if applied:
            world.player.invulnerable = .9
            world.shake = 6
            world.events.append("hurt")
            world.burst(world.player.pos, (255,110,130), 14)
        return applied

    def on_death(self, world):
        world.burst(world.player.pos, world.pak("pilot").color, 35)

    def update(self, world, dt, control):
        self._special_remaining = max(0., self._special_remaining - dt)
        special = control.special and not self._previous_special and self._special_remaining <= 0
        self._previous_special = control.special
        if special:
            self._special_remaining = 2.8
            world.player.invulnerable = max(world.player.invulnerable, .65)
            self.sound.play(volume=.65)
        self.move(world, dt, control, special)

    def move(self, world, dt, control, special):
        self._turn_lock = max(0.,self._turn_lock - dt)
        if special:
            self._direction *= -1
            self._turn_lock = .35
        elif not self._turn_lock and max(abs(control.x),abs(control.y)) > .2:
            self._direction = Vec(1 if control.x>0 else -1,0) if abs(control.x)>abs(control.y) else Vec(0,1 if control.y>0 else -1)
        p = world.player
        p.vel = self._direction * 205
        p.angle = math.atan2(p.vel.y,p.vel.x)
        motion = world.move_body(p,p.vel * dt,p.radius)
        if motion.normals:
            self._direction = self._direction.rotate(90)
    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle) - 90

    def demo_controls(self, world):
        # Ordinary controls trace the perimeter; no capture or enemy state is edited.
        p = world.player
        corners = (Vec(40,40), Vec(WIDTH-40,40), Vec(WIDTH-40,HEIGHT-40), Vec(40,HEIGHT-40))
        if self._demo_entry is None:
            self._demo_entry = Vec(40,p.pos.y)
        target = self._demo_entry if self._demo_corner < 0 else corners[self._demo_corner]
        if p.pos.distance_to(target) < 5:
            self._demo_corner = (self._demo_corner + 1) % 4
            target = corners[self._demo_corner]
        delta = target - p.pos
        if abs(delta.x) > abs(delta.y):
            return Controls(1 if delta.x > 0 else -1, 0, True)
        return Controls(0, 1 if delta.y > 0 else -1, True)
