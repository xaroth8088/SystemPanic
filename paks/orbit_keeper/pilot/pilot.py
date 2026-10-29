"""Orbit Keeper: movement, abilities, private clocks and hit policy."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Pilot, Controls, normalized, unit
from system_panic.pak_api import PilotBase


class OrbitKeeperPilot(PilotBase):
    controls = 'Left / right: orbit. Up / down: step between rings'
    special = 'X: reverse, shield, toggle inward / outward fire'

    def init(self):
        self.spritesheet = self.load_asset('pilot_sheet.png')
        self.dash_sound = self.load_asset("special.ogg")
        self._special_remaining = 0.
        self._dash_remaining = 0.
        self._previous_y = 0.
        self._radial_direction = 0
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

    def sprite(self,world,entity=None):return self.spritesheet

    def sprite_angle(self,world,entity):return -math.degrees(entity.angle)-90.

    def sprite_flip_x(self,world,entity):return False

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
        radial = (1 if control.y > .5 else -1) if abs(control.y) > .5 else 0
        if radial and radial != self._radial_direction:
            rings = (70., 115., 160., 205.)
            index = min(range(len(rings)), key=lambda i: abs(rings[i] - self._orbit_radius))
            self._orbit_radius = rings[max(0, min(len(rings)-1, index + radial))]
            p.pos = world.safe_position(Vec(WIDTH/2, HEIGHT/2) + unit(p.angle)*self._orbit_radius,p.radius)
        self._radial_direction = radial
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

    def demo_controls(self,world):
        from system_panic.model import Controls
        control=self._demo_controls(world) or Controls()
        control.x=int(control.x>.2)-int(control.x<-.2)
        control.y=int(control.y>.2)-int(control.y<-.2)
        return control

    def _demo_controls(self, world):
        if not world.enemies:return Controls(fire=True)
        p=world.player
        target=next((e for e in world.enemies if e.id==self._demo_target and e.health>0),None)
        if target is None:
            target=min(world.enemies,key=lambda e:e.pos.distance_squared_to(p.pos))
            self._demo_target=target.id
        center=Vec(WIDTH/2,HEIGHT/2)
        offset=target.pos+target.vel*.22-center
        # Digital steering has no analog dead zone: counter-steer around the
        # desired ray rather than repeatedly falling back to the idle orbit.
        goal=math.atan2(offset.y,offset.x)+.10
        error=math.atan2(math.sin(goal-p.angle),math.cos(goal-p.angle))
        steering=1 if error>0 else -1
        desired_radius=205. if offset.length()<175 else 70.
        radial=1 if desired_radius-self._orbit_radius>20 else -1 if self._orbit_radius-desired_radius>20 else 0
        # Ring selection is edge-triggered, so insert a neutral frame between steps.
        if self._radial_direction:radial=0
        outward=offset.length()>=self._orbit_radius
        special=outward!=self._fire_outward and self._special_remaining<=0
        return Controls(steering,radial,True,special)

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
