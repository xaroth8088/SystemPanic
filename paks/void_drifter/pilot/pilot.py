"""Void Drifter: movement, abilities, private clocks and hit policy."""
import math
from system_panic.model import Vec, WIDTH, HEIGHT, Pilot, Controls, normalized, unit
from system_panic.pak_api import PilotBase


class VoidDrifterPilot(PilotBase):
    controls = 'Left / right: turn. Up: thrust'
    special = 'X: brake and reverse thrust'

    def init(self):
        self.spritesheet = self.load_asset('pilot_sheet.png')
        self.dash_sound = self.load_asset("special.ogg")
        self._special_remaining = 0.
        self._dash_remaining = 0.
        self._previous_y = 0.
        self._previous_special = False

    def create(self, world, position):
        return Pilot(pos=Vec(position), health=100, max_health=100, radius=11, angle=-math.pi / 2)

    def sprite(self, world, entity=None):
        return self.spritesheet

    def update(self, world, dt, control):
        self._special_remaining = max(0., self._special_remaining - dt)
        self._dash_remaining = max(0., self._dash_remaining - dt)
        jump = control.y < -.5 and self._previous_y >= -.5
        special = control.special and not self._previous_special and self._special_remaining <= 0
        self._previous_y, self._previous_special = control.y, control.special
        if special:
            self._special_remaining = 2.8
            self._dash_remaining = .45
            world.player.invulnerable = max(world.player.invulnerable, .65)
        self.move(world, dt, control, jump, special)

    def move(self, world, dt, control, jump, special):
        if special:
            self.dash_sound.play(volume=.7)
        p = world.player
        p.angle += control.x * 3.7 * dt
        p.vel += unit(p.angle) * (-control.y) * 360 * dt
        p.vel *= math.exp(-.22 * dt)
        if special:
            p.vel *= -.25
        if p.vel.length() > 330:
            p.vel.scale_to_length(330)
        motion = world.move_body(p, p.vel * dt, 12, bounds=None)
        p.pos.x %= WIDTH
        p.pos.y %= HEIGHT
        if motion.blocked_y:
            p.vel.y = 0

    def demo_controls(self, world):
        p = world.player
        target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
        delta = target.pos - p.pos
        vector = normalized(delta)
        special = int(world.time * 3) % 11 == 0
        angle = math.atan2(delta.y, delta.x)
        diff = (angle - p.angle + math.pi) % math.tau - math.pi
        return Controls(max(-1, min(1, diff * 2)), -1 if delta.length() > 180 else .3, True, special)

    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle) - 90

    def on_contact(self, world, enemy, dt):
        if self._dash_remaining > 0:
            world.hit_enemy(enemy, 140 * dt)

    def take_damage(self, world, damage):
        applied = world.apply_damage(world.player, damage)
        if applied:
            world.player.invulnerable = .9
            world.shake = 6
            world.events.append("hurt")
            world.burst(world.player.pos, (255, 110, 130), 14)
        return applied
