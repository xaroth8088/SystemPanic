"""Orbit Keeper: movement, abilities, private clocks and hit policy."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Pilot, Controls, normalized, unit
from system_panic.pak_api import PilotBase


class OrbitKeeperPilot(PilotBase):
    controls = 'Left / right: orbit. Up / down: radius'
    special = 'X: reverse orbit and shield'

    def init(self):
        self.spritesheet = self.load_asset('pilot_sheet.png')
        self.dash_sound = self.load_asset("special.ogg")
        self._special_remaining = 0.
        self._dash_remaining = 0.
        self._previous_y = 0.
        self._previous_special = False
        self._orbit_radius = 170.
        self._orbit_direction = 1

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
        if special:
            self._orbit_direction *= -1
        p.angle += (control.x * 2.2 if control.x else .65 * self._orbit_direction) * dt
        self._orbit_radius = max(70, min(215, self._orbit_radius + control.y * 150 * dt))
        target = Vec(WIDTH / 2, HEIGHT / 2) + unit(p.angle) * self._orbit_radius
        p.vel = (target - p.pos) * 12
        motion = world.move_body(p, p.vel * dt, 12, bounds=pygame.Rect(10, 10, WIDTH - 20, HEIGHT - 20))
        if motion.blocked_y:
            p.vel.y = 0

    def activate(self, world):
        offset = world.player.pos - Vec(WIDTH / 2, HEIGHT / 2)
        world.player.angle = math.atan2(offset.y, offset.x)
        self._orbit_radius = max(80, min(215, offset.length()))

    def demo_controls(self, world):
        p = world.player
        target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
        delta = target.pos - p.pos
        vector = normalized(delta)
        special = int(world.time * 3) % 11 == 0
        steering = .7
        threats = [enemy.pos + enemy.vel * .25 for enemy in world.enemies if enemy.health > 0]
        threats += [shot.pos + shot.vel * .25 for shot in world.projectiles if shot.is_threat_to(world, p)]
        if threats and min(p.pos.distance_to(pos) for pos in threats) < 90:
            steering = max((-.7, .7), key=lambda x: min(
                (Vec(WIDTH / 2, HEIGHT / 2) + unit(p.angle + x * 2.2 * .35) * self._orbit_radius).distance_to(pos)
                for pos in threats))
        return Controls(steering, math.sin(world.time * .7) * .4, True, special)

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
