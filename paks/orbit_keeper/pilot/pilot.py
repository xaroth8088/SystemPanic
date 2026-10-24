"""Orbit Keeper: pilot behavior and local assets."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Beam, Controls, normalized, unit, circle_rect
from system_panic.pak_api import PilotBase


class OrbitKeeperPilot(PilotBase):
    controls = 'Left / right: orbit. Up / down: radius'
    special = 'X: reverse orbit and shield'

    def init(self):
        self.spritesheet = self.load_asset('pilot_sheet.png')
        self.dash_sound = self.load_asset("special.ogg")

    def sprite(self, world, entity=None):
        return self.spritesheet

    def move(self, world, dt, control, jump, special):
        if special:
            self.dash_sound.play(volume=.7)
        p = world.player
        direction = Vec(control.x, control.y)
        if direction.length_squared() > 1:
            direction.normalize_ip()
        if special:
            p.orbit_direction *= -1
        p.angle += (control.x * 2.2 if control.x else .65 * p.orbit_direction) * dt
        p.orbit_radius = max(70, min(215, p.orbit_radius + control.y * 150 * dt))
        target = Vec(WIDTH / 2, HEIGHT / 2) + unit(p.angle) * p.orbit_radius
        p.vel = (target - p.pos) * 12
        world.move_body(p, p.vel * dt, 12)

    def activate(self, world):
        offset = world.player.pos - Vec(WIDTH / 2, HEIGHT / 2)
        world.player.angle = math.atan2(offset.y, offset.x)
        world.player.orbit_radius = max(80, min(215, offset.length()))

    def demo_controls(self, world):
        p = world.player
        target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
        delta = target.pos - p.pos
        vector = normalized(delta)
        special = int(world.time * 3) % 11 == 0
        steering = .7
        threats = [enemy.pos + enemy.vel * .25 for enemy in world.enemies if enemy.health > 0]
        threats += [shot.pos + shot.vel * .25 for shot in world.projectiles if not shot.friendly]
        if threats and min(p.pos.distance_to(pos) for pos in threats) < 90:
            steering = max((-.7, .7), key=lambda x: min(
                (Vec(WIDTH / 2, HEIGHT / 2) + unit(p.angle + x * 2.2 * .35) * p.orbit_radius).distance_to(pos)
                for pos in threats))
        return Controls(steering, math.sin(world.time * .7) * .4, True, special)
