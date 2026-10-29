"""Tide Hopper: raw-input movement and abilities belong to this component."""
import math
import pygame
from system_panic.model import Pilot, Vec, Controls, WIDTH, HEIGHT, unit, normalized, circle_rect
from system_panic.pak_api import PilotBase
from .grid import nearest,clear,passage


class TideHopperPilot(PilotBase):
    controls = 'Arrows / WASD: lane hops (hold to repeat)'
    special = 'X: long ferry hop'

    def init(self):
        self.art = self.load_asset("pilot_sheet.png")
        self.sound = self.load_asset("special.ogg")
        self._previous_special = False
        self._special_remaining = 0.
        self._hop_remaining = 0.
        self._landing = None
        self._travel = 0.

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
        world.player.pos=nearest(world,world.player,world.player.pos)
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
            self.sound.play(volume=.65)
        self.move(world, dt, control, special)

    def move(self, world, dt, control, special):
        p = world.player
        self._hop_remaining = max(0.,self._hop_remaining-dt)
        if self._landing is not None:
            delta = self._landing-p.pos
            step = min(delta.length(),720*dt)
            p.vel = normalized(delta)*720 if delta.length_squared() else Vec()
            motion=world.move_body(p,normalized(delta)*step,p.radius)
            self._travel -= dt
            if delta.length()<=step and not motion.normals:p.pos=self._landing.copy()
            if delta.length()<=step or self._travel<=0 or motion.normals:
                self._landing = None
        else:
            p.vel = Vec()
            if self._hop_remaining<=0 and max(abs(control.x),abs(control.y))>.2:
                direction = Vec(1 if control.x>0 else -1,0) if abs(control.x)>abs(control.y) else Vec(0,1 if control.y>0 else -1)
                distance = 96 if special else 48
                origin=nearest(world,p,p.pos)
                destination=origin+direction*distance
                if not (p.radius<=destination.x<=WIDTH-p.radius and p.radius<=destination.y<=HEIGHT-p.radius):return
                if not clear(world,p,destination) or not passage(world,p,p.pos,destination):return
                self._landing = destination
                self._travel = .24 if special else .13
                self._hop_remaining = .17
                p.angle = math.atan2(direction.y,direction.x)

    def draw(self,graphics,surface,world,*,reduced_motion=False):
        p=world.player
        if world.phase!='active' or world.transition>0 or p.invulnerable<=0 or int(world.time*12)%2 or reduced_motion:
            image=graphics.component_sprite(world,'pilot',p,44)
            surface.blit(image,image.get_rect(center=p.pos))


    def demo_controls(self,world):
        from system_panic.model import Controls
        control=self._demo_controls(world) or Controls()
        control.x=int(control.x>.2)-int(control.x<-.2)
        control.y=int(control.y>.2)-int(control.y<-.2)
        return control

    def _demo_controls(self, world):
        if not world.enemies:return Controls(fire=True)
        target = min(world.enemies,key=lambda e:e.pos.distance_squared_to(world.player.pos))
        delta = target.pos-world.player.pos
        if delta.length()<180: delta=Vec(-delta.y,delta.x)
        return Controls(delta.x,delta.y,True,int(world.time*3)%11==0)
