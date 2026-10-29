"""A controllable kite: steering adds thrust, anchoring trades drift for grip."""
import math
from system_panic.model import Pilot, Vec, Controls, WIDTH, HEIGHT, normalized
from system_panic.pak_api import PilotBase


class KitePilot(PilotBase):
    controls = 'Arrows / WASD: steer the kite'
    special = 'Hold X: anchor against drift'

    def init(self):
        self.art = self.load_asset('pilot_sheet.png')
        self.sound = self.load_asset('special.ogg')
        self.anchor = False
        self.heading = Vec(1, 0)

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
        world.player.invulnerable = max(world.player.invulnerable, 1.4)
        if world.wave > 1:
            world.player.health = min(world.player.max_health, world.player.health + 12)

    def on_shuffle(self, world, changed):
        world.player.invulnerable = max(world.player.invulnerable, 1.)

    def update(self, world, dt, control):
        p = world.player
        direction = Vec(control.x, control.y)
        if direction.length_squared() > 1:
            direction.normalize_ip()
        if direction.length_squared():
            self.heading = direction.copy()
        if control.special and not self.anchor:
            self.sound.play(volume=.32)
        self.anchor = bool(control.special)
        # Anchoring is a locomotion choice, not a shield. External forces can
        # still move the kite, but steering settles much faster.
        p.vel += direction * (1240 if self.anchor else 710) * dt
        p.vel *= math.exp(-(10 if self.anchor else 2.9) * dt)
        cap = 130 if self.anchor else 255
        if p.vel.length_squared() > cap * cap:
            p.vel.scale_to_length(cap)
        motion = world.move_body(p, p.vel * dt, p.radius)
        for normal in motion.normals:
            if p.vel.dot(normal) < 0:
                p.vel -= normal * p.vel.dot(normal)
        p.angle = math.atan2(self.heading.y, self.heading.x)

    def take_damage(self, world, damage):
        applied = world.apply_damage(world.player, damage)
        if applied:
            world.player.invulnerable = .85
            world.shake = 4
            world.events.append('hurt')
            world.burst(world.player.pos, (255, 135, 125), 10)
        return applied

    def on_death(self, world):
        world.burst(world.player.pos, (150, 225, 255), 36)

    def demo_controls(self, world):
        targets = [e for e in world.enemies if e.health > 0]
        if not targets:
            return Controls(fire=True)
        p = world.player
        target = min(targets, key=lambda e: e.pos.distance_squared_to(p.pos))
        delta = target.pos - p.pos
        toward = normalized(delta)
        distance = delta.length()
        tangent = Vec(-toward.y, toward.x)
        direction = toward if distance > 270 else tangent - toward * .25
        for wall in world.geometry:
            if wall.health > 0 and wall.blocks_body(p) and wall.overlaps_circle(p.pos + direction * 45, p.radius + 3):
                center = Vec(wall.rect.center)
                side = 1 if p.pos.y > center.y else -1
                direction = Vec(toward.x * .45, side)
        if p.pos.x < 50: direction.x = 1
        if p.pos.x > WIDTH - 50: direction.x = -1
        if p.pos.y < 50: direction.y = 1
        if p.pos.y > HEIGHT - 50: direction.y = -1
        return Controls((direction.x > .18) - (direction.x < -.18),
                        (direction.y > .18) - (direction.y < -.18), True,
                        distance < 155 and world.time % 2 < .65)
