"""Signal Runner: movement, abilities, private clocks and hit policy."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Pilot
from system_panic.pak_api import PilotBase


class SignalRunnerPilot(PilotBase):
    controls = 'Arrows / WASD: strafe'
    special = 'X: dash through danger'

    def init(self):
        self.spritesheet = self.load_asset('pilot_sheet.png')
        self.dash_sound = self.load_asset("special.ogg")
        self._special_remaining = 0.
        self._dash_remaining = 0.
        self._previous_y = 0.
        self._previous_special = False

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

    def sprite(self,world,entity=None):
        actor=entity if entity is not None else (world.player if world is not None else None)
        angle=actor.angle if actor is not None else 0.
        facing=int((angle+math.tau/16)%math.tau/(math.tau/8))
        phase=int((world.time if world is not None else 0)*8)%4
        return self.spritesheet.frame(phase*8+facing,columns=8,rows=4)

    def sprite_angle(self,world,entity):return 0.

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
        direction = Vec(control.x, control.y)
        if direction.length_squared() > 1:
            direction.normalize_ip()
        p.vel = direction * (640 if self._dash_remaining > 0 else 220)
        if direction.length_squared():
            p.angle = math.atan2(direction.y, direction.x)
        motion = world.move_body(p, p.vel * dt, 12, bounds=pygame.Rect(10, 10, WIDTH - 20, HEIGHT - 20))
        if motion.blocked_y:
            p.vel.y = 0

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

    def demo_controls(self,world):
        from system_panic.model import Controls
        control=self._demo_controls(world) or Controls()
        control.x=int(control.x>.2)-int(control.x<-.2)
        control.y=int(control.y>.2)-int(control.y<-.2)
        return control

    def _demo_controls(self, world):
        # Ordinary-input QA policy, kept with this pilot's movement rules.
        from system_panic.model import Controls, normalized
        if not world.enemies:
            return Controls(fire=True)
        target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(world.player.pos))
        delta = target.pos - world.player.pos
        direction = normalized(delta)
        movement = direction if delta.length() > 210 else Vec(-direction.y, direction.x)
        return Controls(movement.x, movement.y, True, int(world.time * 3) % 11 == 0)
