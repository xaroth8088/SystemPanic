"""Sky Forge: movement, abilities, private clocks and hit policy."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Pilot, Controls, normalized
from system_panic.pak_api import PilotBase


class SkyForgePilot(PilotBase):
    controls = 'Left / right: run. Up: double jump'
    special = 'X: rising forge leap'

    def init(self):
        self.spritesheet = self.load_asset('pilot_sheet.png')
        self.dash_sound = self.load_asset("special.ogg")
        self._special_remaining = 0.
        self._dash_remaining = 0.
        self._previous_y = 0.
        self._previous_special = False
        self._jumps = 0
        self._grounded = False

    def create(self, world, position):
        return Pilot(pos=Vec(position), health=100, max_health=100, radius=11, angle=-math.pi / 2)

    def on_level_start(self, world):
        # Recovery and arrival protection are this pilot's rules, not host defaults.
        if world.wave > 1:
            world.player.health = min(world.player.max_health, world.player.health + 15)
        world.player.invulnerable = max(world.player.invulnerable, 2.)

    def on_shuffle(self, world, changed):
        world.player.invulnerable = max(world.player.invulnerable, 1.5)

    def on_death(self, world):
        world.burst(world.player.pos, world.pak("pilot").color, 35)

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
        direction = Vec(control.x, control.y)
        if direction.length_squared() > 1:
            direction.normalize_ip()
        if jump and self._jumps < 2:
            p.vel.y = -330
            self._jumps += 1
            self._grounded = False
            world.burst(p.pos + Vec(0, 10), world.pak("pilot").color, 6)
        if special:
            p.vel.y = -450
            self._jumps = 1
        p.vel.x = control.x * 220
        p.vel.y = min(460, p.vel.y + 820 * dt)
        if control.x:
            p.angle = 0 if control.x > 0 else math.pi
        motion = world.move_body(p, p.vel * dt, 12, bounds=pygame.Rect(10, 10, WIDTH - 20, HEIGHT - 20))
        if motion.blocked_y:
            p.vel.y = 0
        if motion.landed:
            self._jumps, self._grounded = 0, True

    def demo_controls(self, world):
        if not world.enemies:
            return Controls(fire=True)
        p = world.player
        target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
        delta = target.pos - p.pos
        vector = normalized(delta)
        special = int(world.time * 3) % 11 == 0
        return Controls(vector.x if delta.length() > 180 else -vector.x, -1 if world.time % 1.2 < .15 else 0, True, special)

    def sprite_flip_x(self, world, entity):
        return math.cos(entity.angle) < 0

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
