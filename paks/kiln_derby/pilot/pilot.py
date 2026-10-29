"""A ceramic racer that banks a short draft dash in its current steering direction."""
import math
from system_panic.model import Pilot, Vec, Controls, WIDTH, HEIGHT, normalized
from system_panic.pak_api import PilotBase


class CeramicRacer(PilotBase):
    controls = 'Arrows / WASD: steer'
    special = 'X: draft dash'

    def init(self):
        self.art = self.load_asset('pilot_sheet.png')
        self.sound = self.load_asset('special.ogg')
        self.cooldown = self.dash = 0.
        self.heading = Vec(1, 0)
        self.dash_heading = Vec(1, 0)
        self.previous_special = False

    def create(self, world, position):
        return Pilot(pos=Vec(position), radius=12, health=100, max_health=100)

    def sprite(self, world, entity=None):
        actor=entity if entity is not None else (world.player if world is not None else None)
        angle=actor.angle if actor is not None else 0.
        facing=int((angle+math.tau/16)%math.tau/(math.tau/8))
        phase=int((world.time if world is not None else 0)*8)%4
        return self.art.frame(phase*8+facing, columns=8, rows=4)

    def sprite_angle(self,world,entity):return 0.

    def sprite_flip_x(self,world,entity):return False


    def on_level_start(self, world):
        world.player.invulnerable = max(world.player.invulnerable, 1.5)
        if world.wave > 1:
            world.player.health = min(world.player.max_health, world.player.health + 12)

    def on_shuffle(self, world, changed):
        world.player.invulnerable = max(world.player.invulnerable, 1.2)

    def update(self, world, dt, control):
        self.cooldown = max(0., self.cooldown - dt)
        self.dash = max(0., self.dash - dt)
        p = world.player
        direction = Vec(control.x, control.y)
        if direction.length_squared() > 1:
            direction.normalize_ip()
        if direction.length_squared():
            self.heading = direction.copy()
        if control.special and not self.previous_special and self.cooldown <= 0:
            self.cooldown, self.dash = 2.1, .22
            self.dash_heading = self.heading.copy()
            p.invulnerable = max(p.invulnerable, .26)
            self.sound.play(volume=.4)
            world.burst(p.pos, (255, 187, 110), 7)
        self.previous_special = bool(control.special)
        desired = self.dash_heading * 550 if self.dash else direction * 225
        p.vel = p.vel.lerp(desired, 1 - math.exp(-(18 if self.dash else 10) * dt))
        motion = world.move_body(p, p.vel * dt, p.radius)
        for normal in motion.normals:
            if p.vel.dot(normal) < 0:
                p.vel -= normal * p.vel.dot(normal)
        p.angle = math.atan2(self.heading.y, self.heading.x)

    def take_damage(self, world, damage):
        applied = world.apply_damage(world.player, damage)
        if applied:
            world.player.invulnerable = .8
            world.shake = 4
            world.events.append('hurt')
            world.burst(world.player.pos, (255, 120, 100), 12)
        return applied

    def on_death(self, world):
        world.burst(world.player.pos, (255, 173, 101), 35)

    def demo_controls(self, world):
        targets = [e for e in world.enemies if e.health > 0]
        if not targets:
            return Controls(fire=True)
        p = world.player
        target = min(targets, key=lambda e: e.pos.distance_squared_to(p.pos))
        delta = target.pos - p.pos
        toward = normalized(delta)
        distance = delta.length()
        direction = toward if distance > 245 else Vec(-toward.y, toward.x) * .9 - toward * .3
        for wall in world.geometry:
            if wall.health > 0 and wall.blocks_body(p) and wall.overlaps_circle(p.pos+direction*45, p.radius+5):
                center = Vec(wall.rect.center)
                if abs(p.pos.x - center.x) < abs(p.pos.y - center.y):
                    direction = Vec(1 if target.pos.x > p.pos.x else -1, direction.y*.3)
                else:
                    direction = Vec(direction.x*.3, 1 if p.pos.y > center.y else -1)
        if p.pos.x < 55: direction.x = 1
        if p.pos.x > WIDTH - 55: direction.x = -1
        if p.pos.y < 55: direction.y = 1
        if p.pos.y > HEIGHT - 55: direction.y = -1
        for shot in world.projectiles:
            if shot.alive and shot.is_threat_to(world, p) and shot.pos.distance_to(p.pos) < 90:
                direction += normalized(p.pos - shot.pos) * 1.5
        return Controls((direction.x > .18) - (direction.x < -.18),
                        (direction.y > .18) - (direction.y < -.18), True,
                        distance < 95 or world.time % 3.5 < .04)
