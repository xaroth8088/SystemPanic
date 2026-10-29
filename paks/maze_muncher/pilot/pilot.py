"""Maze Muncher: raw-input movement and abilities belong to this component."""
import math
import pygame
from system_panic.model import Pilot, Vec, Controls, WIDTH, HEIGHT, unit, normalized, circle_rect
from system_panic.pak_api import PilotBase
from .navigation import Route,move,grid_position


class MazeMuncherPilot(PilotBase):
    controls = 'Arrows / WASD: buffered cardinal turns'
    special = 'X: energized contact chomp'

    def init(self):
        self.art = self.load_asset("pilot_sheet.png")
        self.sound = self.load_asset("special.ogg")
        self._previous_special = False
        self._special_remaining = 0.
        self._direction = Vec(1,0)
        self._wanted = Vec(1,0)
        self._energized = 0.
        self._blocked = False
        self._route=Route()
        self._demo_next=0.
        self._demo_direction=Vec(1,0)

    def sprite(self,world,entity=None):
        actor=entity if entity is not None else (world.player if world is not None else None)
        angle=actor.angle if actor is not None else 0.
        facing=int((angle+math.tau/8)%math.tau/(math.tau/4))
        phase=int((world.time if world is not None else 0)*8)%4
        return self.art.frame(phase*4+facing,columns=4,rows=4)

    def sprite_angle(self,world,entity):return 0.

    def sprite_flip_x(self,world,entity):return False





    def create(self, world, position):
        return Pilot(pos=Vec(position), health=100, max_health=100, radius=11, angle=-math.pi / 2)

    def on_level_start(self, world):
        world.player.pos=grid_position(world,world.player.pos,world.player)
        self._route.waypoint=None
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
        self._energized = max(0., self._energized - dt)
        if special: self._energized = 1.15
        x, y = control.x, control.y
        if max(abs(x),abs(y)) > .15:
            self._wanted = Vec(1 if x > 0 else -1,0) if abs(x) > abs(y) else Vec(0,1 if y > 0 else -1)
        p = world.player
        speed = 235 if self._energized else 200
        same_axis = self._direction.x * self._wanted.x != 0 or self._direction.y * self._wanted.y != 0
        coordinate = p.pos.y if self._wanted.x else p.pos.x
        snapped = 16+round((coordinate-16) / 32) * 32
        near_corner = abs(coordinate - snapped) <= speed * dt + 2
        if same_axis or near_corner or self._blocked:
            if not same_axis and near_corner:
                candidate=p.pos.copy()
                if self._wanted.x:candidate.y=snapped
                else:candidate.x=snapped
                if not any(w.health>0 and w.blocks_body(p) and w.overlaps_circle(candidate,p.radius) for w in world.geometry):p.pos=candidate
            self._direction = self._wanted.copy()
        p.vel = self._direction * speed
        p.angle = math.atan2(p.vel.y,p.vel.x)
        self._blocked = bool(move(world,p,p.vel * dt,p.radius).normals)

    def on_contact(self, world, enemy, dt):
        if self._energized:
            world.hit_enemy(enemy, 180 * dt)


    def demo_controls(self,world):
        from system_panic.model import Controls
        control=self._demo_controls(world) or Controls()
        control.x=int(control.x>.2)-int(control.x<-.2)
        control.y=int(control.y>.2)-int(control.y<-.2)
        return control

    def _demo_controls(self, world):
        if not world.enemies: return Controls(fire=True)
        target = min(world.enemies,key=lambda e:e.pos.distance_squared_to(world.player.pos))
        if world.time>=self._demo_next:
            self._demo_next=world.time+.008
            self._demo_direction=self._route.direction(world,target.pos)
        near=world.player.pos.distance_to(target.pos)<120
        return Controls(self._demo_direction.x,self._demo_direction.y,near,near and self._special_remaining<=0 and not self._previous_special)
