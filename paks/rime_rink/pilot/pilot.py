"""Acceleration and a deliberate skate brake; all inputs are digital directions."""
import math
from system_panic.model import Pilot, Vec, Controls, normalized
from system_panic.pak_api import PilotBase


class Skater(PilotBase):
    controls = "Arrows / WASD: accelerate on ice"
    special = "Hold X: carve brake and grip"

    def init(self):
        self.art = self.load_asset("pilot_sheet.png")
        self.sound = self.load_asset("special.ogg")
        self.braking = False

    def create(self, world, position):
        return Pilot(pos=Vec(position), radius=14, health=100, max_health=100)

    def sprite(self, world, entity=None):
        actor=entity if entity is not None else (world.player if world is not None else None)
        angle=actor.angle if actor is not None else 0.
        facing=int((angle+math.tau/16)%math.tau/(math.tau/8))
        phase=int((world.time if world is not None else 0)*8)%4
        return self.art.frame(phase*8+facing, columns=8, rows=4)

    def sprite_angle(self,world,entity):return 0.

    def sprite_flip_x(self,world,entity):return False


    def on_level_start(self, world):
        if world.wave > 1:
            world.player.health = min(world.player.max_health, world.player.health + 14)
        world.player.invulnerable = max(world.player.invulnerable, 1.7)

    def on_shuffle(self, world, changed):
        world.player.invulnerable = max(world.player.invulnerable, 1.2)

    def update(self, world, dt, control):
        p = world.player
        direction = Vec(control.x, control.y)
        if direction.length_squared() > 1:
            direction.normalize_ip()
        if control.special and not self.braking:
            self.sound.play(volume=.4)
            world.burst(p.pos, (177, 230, 255), 8)
        self.braking = bool(control.special)
        p.vel *= math.exp(-(7.5 if self.braking else .65) * dt)
        p.vel += direction * (720 if self.braking else 510) * dt
        limit = 115 if self.braking else 290
        if p.vel.length_squared() > limit * limit:
            p.vel.scale_to_length(limit)
        if direction.length_squared():
            p.angle = math.atan2(direction.y, direction.x)
        motion = world.move_body(p, p.vel * dt, p.radius)
        for normal in motion.normals:
            if p.vel.dot(normal) < 0:
                p.vel -= 1.55 * p.vel.dot(normal) * normal

    def take_damage(self, world, damage):
        applied = world.apply_damage(world.player, damage)
        if applied:
            world.player.invulnerable = .85
            world.shake = 5
            world.events.append("hurt")
            world.burst(world.player.pos, (255, 161, 143), 10)
        return applied

    def on_death(self, world):
        world.burst(world.player.pos, (132, 215, 255), 26)

    def demo_controls(self, world):
        if not world.enemies:
            return Controls(fire=True)
        p = world.player
        target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
        delta = target.pos - p.pos
        toward = normalized(delta)
        distance = delta.length()
        direction = toward if distance > 205 else -toward if distance < 125 else Vec(-toward.y, toward.x)
        for angle in (0, 45, -45, 90, -90):
            trial = direction.rotate(angle)
            probe = p.pos + trial * 65
            if not any(w.health > 0 and w.blocks_body(p) and w.overlaps_circle(probe, p.radius + 4) for w in world.geometry):
                direction = trial
                break
        # Oppose momentum before accelerating through a close pursuer.
        desired = direction * 200 - p.vel * .6
        return Controls((desired.x > 25) - (desired.x < -25), (desired.y > 25) - (desired.y < -25), True, distance < 120)
