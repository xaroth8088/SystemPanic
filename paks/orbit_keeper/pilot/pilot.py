"""Orbit Keeper: movement, abilities, private clocks and hit policy."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Pilot, Controls, normalized, unit
from system_panic.pak_api import PilotBase


class OrbitKeeperPilot(PilotBase):
    controls = 'Left / right: orbit. Up / down: radius'
    special = 'X: reverse, shield, toggle inward / outward fire'

    def init(self):
        self.spritesheet = self.load_asset('pilot_sheet.png')
        self.dash_sound = self.load_asset("special.ogg")
        self._special_remaining = 0.
        self._dash_remaining = 0.
        self._previous_y = 0.
        self._previous_special = False
        self._orbit_radius = 170.
        self._orbit_direction = 1
        self._fire_outward = True
        self._demo_target = None

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
        if special:
            self._orbit_direction *= -1
            self._fire_outward = not self._fire_outward
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

    def aim_direction(self, world):
        radial = normalized(world.player.pos - Vec(WIDTH / 2, HEIGHT / 2), unit(world.player.angle))
        return radial * (1 if self._fire_outward else -1)

    def status(self, world):
        return "FIRE OUTWARD" if self._fire_outward else "FIRE INWARD"

    def demo_controls(self, world):
        if not world.enemies:
            return Controls(fire=True)
        p = world.player
        target = next((e for e in world.enemies if e.id == self._demo_target and e.health > 0), None)
        if target is None:
            target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
            self._demo_target = target.id
        center = Vec(WIDTH / 2, HEIGHT / 2)
        future = target.pos + target.vel * .25
        offset = future - center
        goal_angle = math.atan2(offset.y, offset.x)
        error = math.atan2(math.sin(goal_angle - p.angle), math.cos(goal_angle - p.angle))
        steering = max(-.85, min(.85, error * 2.6))
        desired_radius = max(80, min(215, offset.length() + 110 if offset.length() < 150 else offset.length() - 110))
        radial = max(-1., min(1., (desired_radius - self._orbit_radius) / 60))
        outward = target.pos.distance_to(center) >= p.pos.distance_to(center)
        special = outward != self._fire_outward and self._special_remaining <= 0
        threats = [enemy.pos + enemy.vel * .25 for enemy in world.enemies if enemy.health > 0]
        threats += [shot.pos + shot.vel * .25 for shot in world.projectiles if shot.is_threat_to(world, p)]
        if threats:
            def option(action):
                x,y=action
                radius=max(70,min(215,self._orbit_radius+y*150*.25))
                destination=center+unit(p.angle+x*2.2*.25)*radius
                danger=sum(max(0.,55-destination.distance_to(pos))**2 for pos in threats)
                angle_error=abs(math.atan2(math.sin(goal_angle-(p.angle+x*2.2*.25)),math.cos(goal_angle-(p.angle+x*2.2*.25))))
                return -danger*2-angle_error*70-abs(radius-desired_radius)*.35
            steering,radial=max(((steering,radial),(-.9,0),(.9,0),(steering,-1),(steering,1)),key=option)
            if min(p.pos.distance_to(pos) for pos in threats)<30 and self._special_remaining<=0:
                special=not self._previous_special
        return Controls(steering, radial, True, special)

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
