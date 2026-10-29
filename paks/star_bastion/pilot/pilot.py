"""Star Bastion: raw-input movement and abilities belong to this component."""
import math
import pygame
from system_panic.model import Pilot, Vec, Controls, WIDTH, HEIGHT, unit, normalized, circle_rect
from system_panic.pak_api import PilotBase


class StarBastionPilot(PilotBase):
    controls = 'Left / right: move along the bottom'
    special = 'X: barrel roll across the firing line'

    def init(self):
        self.art = self.load_asset("pilot_sheet.png")
        self.sound = self.load_asset("special.ogg")
        self._previous_special = False
        self._special_remaining = 0.
        self._roll = 0.

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0)*8)%4,columns=4)

    def create(self, world, position):
        return Pilot(pos=Vec(position.x, HEIGHT - 24), health=100, max_health=100, radius=11, angle=-math.pi / 2)

    def settle(self, world):
        # Search only this lane: arbitrary mixed cover must not lift the ship.
        p = world.player
        y = HEIGHT - 24
        candidates = [max(p.radius, min(WIDTH - p.radius, p.pos.x))]
        candidates += sorted(range(16, WIDTH - 15, 8), key=lambda x: abs(x - p.pos.x))
        for x in candidates:
            point = Vec(x, y)
            if not any(w.health > 0 and w.blocks_body(p) and w.overlaps_circle(point, p.radius + 2) for w in world.geometry):
                p.pos = point
                return

    def on_level_start(self, world):
        if world.wave > 1:
            world.player.health = min(world.player.max_health, world.player.health + 15)
        world.player.invulnerable = max(world.player.invulnerable, 2.)
        self.settle(world)

    def on_shuffle(self, world, changed):
        world.player.invulnerable = max(world.player.invulnerable, 1.5)
        self.settle(world)

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
        p = world.player
        self._roll = max(0.,self._roll-dt)
        if special: self._roll = .4
        p.pos.y = HEIGHT - 24
        p.vel = Vec(control.x * (570 if self._roll else 270), 0)
        world.move_body(p,p.vel*dt,p.radius,bounds=pygame.Rect(12,HEIGHT//2-20,WIDTH-24,HEIGHT//2+8))
        p.pos.y = HEIGHT - 24
        p.angle = -math.pi/2

    def demo_controls(self,world):
        from system_panic.model import Controls
        control=self._demo_controls(world) or Controls()
        control.x=int(control.x>.2)-int(control.x<-.2)
        control.y=int(control.y>.2)-int(control.y<-.2)
        return control

    def _demo_controls(self, world):
        if not world.enemies: return Controls(fire=True)
        target = min(world.enemies,key=lambda e:e.pos.distance_squared_to(world.player.pos))
        return Controls(max(-1,min(1,(target.pos.x-world.player.pos.x)/120)),0,True,int(world.time*3)%11==0)
