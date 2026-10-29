"""Vector Coil: raw-input movement and abilities belong to this component."""
import math
import pygame
from system_panic.model import Pilot, Vec, Controls, WIDTH, HEIGHT, unit, normalized, circle_rect
from system_panic.pak_api import PilotBase
from .navigation import Route


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
        self._entry_route=Route()
        self._demo_next=0.
        self._demo_direction=Vec(1,0)
        self._demo_corner = -1
        self._demo_entry = None

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
        self._demo_corner=-1
        self._demo_entry=None
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

    def demo_controls(self,world):
        from system_panic.model import Controls
        control=self._demo_controls(world) or Controls()
        control.x=int(control.x>.2)-int(control.x<-.2)
        control.y=int(control.y>.2)-int(control.y<-.2)
        return control

    def _demo_controls(self, world):
        # Ordinary controls trace the perimeter; no capture or enemy state is edited.
        p = world.player
        corners = (Vec(16,16), Vec(WIDTH-16,16), Vec(WIDTH-16,HEIGHT-16), Vec(16,HEIGHT-16))
        if self._demo_entry is None:
            # Travel without drawing to the nearest outer corner, then start
            # a clean circuit. Starting mid-arena creates accidental small loops.
            self._demo_entry=min(corners,key=lambda c:c.distance_squared_to(p.pos)).copy()
            self._demo_corner=-1
        target = self._demo_entry if self._demo_corner < 0 else corners[self._demo_corner]
        if p.pos.distance_to(target) < 5:
            self._demo_corner = (corners.index(self._demo_entry)+1)%4 if self._demo_corner<0 else (self._demo_corner + 1) % 4
            target = corners[self._demo_corner]
        if self._demo_corner<0:
            if world.time>=self._demo_next:
                self._demo_next=world.time+.008
                self._demo_direction=self._entry_route.direction(world,target)
            return Controls(self._demo_direction.x,self._demo_direction.y,False)
        delta=target-p.pos
        # Finish each edge before turning; digital diagonal ties otherwise cut
        # corners and repeatedly miss the intended crossing point.
        if self._demo_corner in (0,2):
            if abs(delta.x)>4:return Controls(1 if delta.x>0 else -1,0,True)
            return Controls(0,1 if delta.y>0 else -1,True)
        if abs(delta.y)>4:return Controls(0,1 if delta.y>0 else -1,True)
        return Controls(1 if delta.x>0 else -1,0,True)
