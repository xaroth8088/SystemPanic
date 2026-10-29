"""Neon Breach: raw-input movement and abilities belong to this component."""
import math
from dataclasses import dataclass
import pygame
from system_panic.model import Pilot, Vec, Controls, WIDTH, HEIGHT, unit, normalized, circle_rect
from system_panic.pak_api import PilotBase

@dataclass
class Paddle(Pilot):
    edge: int = 0
    def footprint(self):
        width,height=(84,24) if self.edge in (0,2) else (24,84)
        return pygame.Rect(round(self.pos.x-width/2),round(self.pos.y-height/2),width,height)
    def overlaps_circle(self,position,radius):return circle_rect(position,radius,self.footprint())


class NeonBreachPilot(PilotBase):
    controls = 'Left / right: perimeter slide. Up / down: unused'
    special = 'X: magnetic corner burst'

    def init(self):
        self.art = self.load_asset("pilot_sheet.png")
        self.sound = self.load_asset("special.ogg")
        self._previous_special = False
        self._special_remaining = 0.
        self._distance = 0.
        self._edge_y = 0.
        self._boost = 0.

    def sprite(self,world,entity=None):
        actor=entity if entity is not None else (world.player if world is not None else None)
        angle=actor.angle if actor is not None else 0.
        facing=int((angle+math.tau/8)%math.tau/(math.tau/4))
        if actor is not None:
            facing=(1,2,3,0)[actor.edge]
        phase=int((world.time if world is not None else 0)*8)%4
        return self.art.frame(phase*4+facing,columns=4,rows=4)

    def sprite_angle(self,world,entity):return 0.

    def sprite_flip_x(self,world,entity):return False



    def create(self, world, position):
        return Paddle(pos=Vec(position), health=100, max_health=100, radius=11, angle=math.pi/2)

    def draw(self,graphics,surface,world,*,reduced_motion=False):
        p=world.player
        if p.invulnerable>0 and world.phase=='active' and world.transition<=0 and not int(world.time*12)%2 and not reduced_motion:return
        image=graphics.component_sprite(world,'pilot',p,44)
        bounds=image.get_bounding_rect(min_alpha=32)
        image=pygame.transform.scale(image.subsurface(bounds),(84,24))
        if p.edge in (1,3):image=pygame.transform.rotate(image,90 if p.edge==3 else -90)
        surface.blit(image,image.get_rect(center=p.pos))

    def on_level_start(self, world):
        self.move(world,0,Controls(),False)
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

    def activate(self, world):
        p = world.player.pos
        self._distance = p.x - 12 if p.y < HEIGHT / 2 else (WIDTH - 24) + (HEIGHT - 24) + WIDTH - 12 - p.x
        self.move(world,0,Controls(),False)

    def move(self, world, dt, control, special):
        w, h = WIDTH - 24, HEIGHT - 24
        self._boost = max(0., self._boost - dt)
        if special:
            self._boost = .5
            self._distance += 70
        self._distance = (self._distance + control.x * (560 if self._boost else 250) * dt) % (2 * (w + h))
        d = self._distance
        if d < w: target,edge = Vec(12 + d,12),0
        elif d < w + h: target,edge = Vec(WIDTH-12,12+d-w),1
        elif d < 2 * w + h: target,edge = Vec(WIDTH-12-(d-w-h),HEIGHT-12),2
        else: target,edge = Vec(12,HEIGHT-12-(d-2*w-h)),3
        previous = world.player.pos.copy()
        world.player.pos = world.safe_position(target, world.player.radius)
        world.player.vel = (world.player.pos - previous) / dt if dt else Vec()
        world.player.edge=edge
        world.player.angle=(math.pi/2,math.pi,-math.pi/2,0)[edge]


    def demo_controls(self,world):
        from system_panic.model import Controls
        control=self._demo_controls(world) or Controls()
        control.x=int(control.x>.2)-int(control.x<-.2)
        control.y=int(control.y>.2)-int(control.y<-.2)
        return control

    def _demo_controls(self, world):
        return Controls(.85, 0, True, int(world.time * 3) % 11 == 0)
