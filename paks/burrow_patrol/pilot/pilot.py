"""Burrow Patrol: raw-input movement and abilities belong to this component."""
import math
import pygame
from system_panic.model import Pilot, Vec, Controls, WIDTH, HEIGHT, unit, normalized, circle_rect
from system_panic.pak_api import PilotBase


class BurrowPatrolPilot(PilotBase):
    controls = 'Arrows / WASD: cardinal digging'
    special = 'X: drill burst through nearby rock'

    def init(self):
        self.art = self.load_asset("pilot_sheet.png")
        self.sound = self.load_asset("special.ogg")
        self._previous_special = False
        self._special_remaining = 0.
        self._boost = 0.
        self._demo_kills = -1
        self._demo_progress = 0.

    def sprite(self, world, entity=None):
        return self.art

    def create(self, world, position):
        return Pilot(pos=Vec(position), health=100, max_health=100, radius=11, angle=-math.pi / 2)

    def on_level_start(self, world):
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
        p = world.player
        self._boost = max(0.,self._boost - dt)
        if special:
            self._boost = .8
            for wall in world.geometry:
                if circle_rect(p.pos,75,wall.rect): world.hit_cover(wall, 75)
            for enemy in world.enemies:
                if enemy.pos.distance_to(p.pos)<75+enemy.radius:
                    world.hit_enemy(enemy,38)
            world.burst(p.pos,world.pak("pilot").color,18)
        x,y = control.x,control.y
        direction = Vec()
        if max(abs(x),abs(y)) > .15:
            direction = Vec(1 if x>0 else -1,0) if abs(x)>abs(y) else Vec(0,1 if y>0 else -1)
        p.vel = direction * (310 if self._boost else 185)
        if direction.length_squared():
            p.angle = math.atan2(direction.y,direction.x)
            for wall in world.geometry:
                if circle_rect(p.pos + direction * 22,16,wall.rect): world.hit_cover(wall, 135 * dt)
        world.move_body(p,p.vel * dt,p.radius)

    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle)

    def demo_controls(self, world):
        if not world.enemies: return Controls(fire=True)
        p=world.player
        if world.kills!=self._demo_kills:
            self._demo_kills=world.kills
            self._demo_progress=world.time
        close_gap=world.time-self._demo_progress>4
        threats=[e.pos+e.vel*.35 for e in world.enemies if e.health>0]
        def safety(direction):
            destination=p.pos+direction*140
            if not (30<destination.x<WIDTH-30 and 30<destination.y<HEIGHT-30): return -10000
            clearance=min(destination.distance_to(t) for t in threats)
            # Keep pumping distance without trying to ram the inflated target.
            obstruction=80 if any(w.health>0 and w.overlaps_segment(p.pos,destination) for w in world.geometry) else 0
            spacing=-abs(clearance-240)+min(clearance,100)*.2 if close_gap else clearance-abs(clearance-340)*.3
            return spacing-destination.distance_to(Vec(WIDTH/2,HEIGHT/2))*.18-obstruction
        direction=max((Vec(1,0),Vec(-1,0),Vec(0,1),Vec(0,-1)),key=safety)
        special=min(p.pos.distance_to(t) for t in threats)<125 and self._special_remaining<=0 and not self._previous_special
        return Controls(direction.x,direction.y,True,special)
