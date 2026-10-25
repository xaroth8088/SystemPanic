"""Vector Coil: raw-input movement and abilities belong to this component."""
import math
import pygame
from system_panic.model import Pilot, Vec, Controls, WIDTH, HEIGHT, unit, normalized, circle_rect
from system_panic.pak_api import PilotBase, EffectBase


class VectorCoilPilot(PilotBase):
    controls = 'Arrows / WASD: right-angle trail turns'
    special = 'X: reverse the trail and shield'

    def init(self):
        self.art = self.load_asset("pilot_sheet.png")
        self.sound = self.load_asset("special.ogg")
        self._previous_special = False
        self._special_remaining = 0.
        self._direction = Vec(1,0)
        self._turn_lock = 0.
        self._trail = []
        self._trace = None

    def sprite(self, world, entity=None):
        return self.art

    def create(self, world, position):
        return Pilot(pos=Vec(position), health=100, max_health=100, radius=11, angle=-math.pi / 2)

    def on_level_start(self, world):
        if world.wave > 1:
            world.player.health = min(world.player.max_health, world.player.health + 15)
        world.player.invulnerable = max(world.player.invulnerable, 2.)
        self._trail.clear()

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
        self._trail = [(pos,life-dt) for pos,life in self._trail if life > dt]
        if not self._trail or self._trail[-1][0].distance_to(p.pos)>14:
            self._trail.append((p.pos.copy(),2.8))
        self._trail = self._trail[-40:]
        if self._trace is None or not self._trace.alive:
            self._trace = TrailImage()
            world.effects.append(self._trace)
        self._trace.points = [pos.copy() for pos,life in self._trail]
        self._trace.color = world.pak("pilot").color
        self._trace.remaining = .05
        for enemy in world.enemies:
            if any(enemy.pos.distance_to(pos)<enemy.radius+6 for pos,_ in self._trail):
                world.hit_enemy(enemy,40*dt)

    def sprite_angle(self, world, entity):
        return -math.degrees(entity.angle) - 90

    def demo_controls(self, world):
        if not world.enemies: return Controls(fire=True)
        target=min(world.enemies,key=lambda e:e.pos.distance_squared_to(world.player.pos))
        delta=target.pos-world.player.pos
        if delta.length()<200: delta=Vec(-delta.y,delta.x)
        return Controls(delta.x,delta.y,True,int(world.time*3)%11==0)


class TrailImage(EffectBase):
    def __init__(self):
        self.points = []
        self.color = (185,246,66)
        self.remaining = .05
        self.alive = True

    def update(self,dt):
        self.remaining -= dt
        self.alive = self.remaining > 0

    def draw(self,graphics,surface,world):
        if len(self.points)>1:
            pygame.draw.lines(surface,self.color,False,self.points,2)
