"""Tide Hopper: raw-input movement and abilities belong to this component."""
import math
import pygame
from system_panic.model import Pilot, Vec, Controls, WIDTH, HEIGHT, unit, normalized, circle_rect
from system_panic.pak_api import PilotBase


class TideHopperPilot(PilotBase):
    controls = 'Arrows / WASD: lane hops (hold to repeat)'
    special = 'X: long protected ferry hop'

    def init(self):
        self.art = self.load_asset("pilot_sheet.png")
        self.sound = self.load_asset("special.ogg")
        self._previous_special = False
        self._special_remaining = 0.
        self._hop_remaining = 0.
        self._landing = None
        self._travel = 0.

    def sprite(self, world, entity=None):
        return self.art

    def create(self, world, position):
        return Pilot(pos=Vec(position), health=100, max_health=100, radius=11, angle=-math.pi / 2)

    def on_level_start(self, world):
        if world.wave > 1:
            world.player.health = min(world.player.max_health, world.player.health + 15)
        world.player.invulnerable = max(world.player.invulnerable, 2.)
        self._landing = None

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
        p = world.player
        self._hop_remaining = max(0.,self._hop_remaining-dt)
        if self._landing is not None:
            delta = self._landing-p.pos
            step = min(delta.length(),720*dt)
            p.vel = normalized(delta)*720 if delta.length_squared() else Vec()
            world.move_body(p,normalized(delta)*step,p.radius)
            self._travel -= dt
            if delta.length()<3 or self._travel<=0:
                self._landing = None
        else:
            p.vel = Vec()
            if self._hop_remaining<=0 and max(abs(control.x),abs(control.y))>.2:
                direction = Vec(1 if control.x>0 else -1,0) if abs(control.x)>abs(control.y) else Vec(0,1 if control.y>0 else -1)
                distance = 112 if special else 48
                self._landing = world.safe_position(p.pos+direction*distance,p.radius)
                self._travel = .22 if special else .11
                self._hop_remaining = .17
                p.angle = math.atan2(direction.y,direction.x)
                p.invulnerable = max(p.invulnerable,.08)

    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle) - 90

    def demo_controls(self, world):
        if not world.enemies:return Controls(fire=True)
        target = min(world.enemies,key=lambda e:e.pos.distance_squared_to(world.player.pos))
        delta = target.pos-world.player.pos
        if delta.length()<180: delta=Vec(-delta.y,delta.x)
        return Controls(delta.x,delta.y,True,int(world.time*3)%11==0)
