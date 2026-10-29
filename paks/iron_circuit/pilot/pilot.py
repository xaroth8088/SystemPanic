"""Iron Circuit: movement, abilities, private clocks and hit policy."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Pilot, Controls, normalized, unit
from system_panic.pak_api import PilotBase


class IronCircuitPilot(PilotBase):
    controls = 'Left / right: steer. Up / down: speed'
    special = 'X: overdrive and ram'

    def init(self):
        self.spritesheet = self.load_asset('pilot_sheet.png')
        self.dash_sound = self.load_asset("special.ogg")
        self._special_remaining = 0.
        self._dash_remaining = 0.
        self._previous_y = 0.
        self._previous_special = False
        self._speed=90.

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
        p.angle += control.x * 2.9 * dt
        top=430. if self._dash_remaining>0 else 340.
        acceleration=180. if self._dash_remaining>0 else 105. if control.y<-.5 else 75.
        self._speed=max(65.,min(top,self._speed+(-180. if control.y>.5 else acceleration)*dt))
        speed=self._speed
        p.vel = unit(p.angle) * speed
        old = p.pos.copy()
        motion = world.move_body(p, p.vel * dt, 12, bounds=pygame.Rect(10, 10, WIDTH - 20, HEIGHT - 20))
        if dt>0:
            p.vel=(p.pos-old)/dt
        if motion.normals:
            fraction=min(1.,p.vel.length()/max(1.,speed))
            self._speed=max(40.,self._speed*(.55+.45*fraction))

    def demo_controls(self,world):
        from system_panic.model import Controls
        control=self._demo_controls(world) or Controls()
        control.x=int(control.x>.2)-int(control.x<-.2)
        control.y=int(control.y>.2)-int(control.y<-.2)
        return control

    def _demo_controls(self, world):
        if not world.enemies:
            return Controls(fire=True)
        p = world.player
        target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
        def clearance(steer):
            point=p.pos.copy()
            for step in range(1,13):
                heading=p.angle+steer*2.9*step*.045
                point+=unit(heading)*max(100,self._speed)*.045
                if not (24<point.x<WIDTH-24 and 24<point.y<HEIGHT-24) or any(w.health>0 and w.blocks_body(p) and w.overlaps_circle(point,15) for w in world.geometry):return step
            return 13-point.distance_to(target.pos)*.0005
        steer=max((-1,0,1),key=clearance)
        special=self._speed>180 and clearance(steer)>12 and not self._previous_special
        return Controls(steer,-1,True,special)


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
