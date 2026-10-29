"""Sky Forge: movement, abilities, private clocks and hit policy."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, Pilot, Controls, Cover, normalized
from system_panic.pak_api import PilotBase


class SkyForgePilot(PilotBase):
    controls = 'Left / right: run. Up: double jump'
    special = 'X: rising forge leap'

    def init(self):
        self.spritesheet = self.load_asset('pilot_sheet.png')
        self.dash_sound = self.load_asset("special.ogg")
        self._special_remaining = 0.
        self._dash_remaining = 0.
        self._previous_y = 0.
        self._previous_special = False
        self._jumps = 0
        self._grounded = False
        self._demo_drop_direction=0
        self._demo_drop_top=0.

    def create(self, world, position):
        return Pilot(pos=Vec(position), health=100, max_health=100, radius=22, angle=-math.pi / 2)

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
        facing=0 if math.cos(angle)>=0 else 1
        phase=int((world.time if world is not None else 0)*8)%4
        if world is not None:phase=phase%3 if self._grounded else 3
        return self.spritesheet.frame(phase*2+facing,columns=2,rows=4)

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
        if jump and self._jumps < 2:
            p.vel.y = -330
            self._jumps += 1
            self._grounded = False
            world.burst(p.pos + Vec(0, 10), world.pak("pilot").color, 6)
        if special:
            p.vel.y = -450
            self._jumps = 1
        p.vel.x = control.x * 220
        p.vel.y = min(460, p.vel.y + 820 * dt)
        if control.x:
            p.angle = 0 if control.x > 0 else math.pi
        bounds = pygame.Rect(10, 10, WIDTH - 20, HEIGHT - 10)
        horizontal = world.move_body(p, Vec(p.vel.x * dt, 0), p.radius, bounds=bounds)
        displacement = Vec(0, p.vel.y * dt)
        # Flat feet on rectangular decks: a circular corner landing otherwise
        # leaves the pilot below the deck top, unable to walk inward. Custom
        # shapes retain their own collision protocol rather than using rect bounds.
        deck = None
        for wall in world.geometry:
            if type(wall) is not Cover or wall.health <= 0 or not wall.blocks_body(p):
                continue
            top = wall.rect.top - p.radius
            if (p.vel.y >= 0 and p.pos.y <= top <= p.pos.y + displacement.y
                    and wall.rect.left - p.radius < p.pos.x < wall.rect.right + p.radius):
                displacement.y = top - p.pos.y
                deck = wall
        motion = world.move_body(p, displacement, p.radius, bounds=bounds)
        landed_on_deck = deck is not None and abs(p.pos.y - (deck.rect.top - p.radius)) < 1e-6
        if horizontal.blocked_y or motion.blocked_y or landed_on_deck:
            p.vel.y = 0
        if horizontal.landed or motion.landed or landed_on_deck:
            self._jumps, self._grounded = 0, True

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
        delta = target.pos - p.pos
        if self._demo_drop_direction:
            if p.pos.y<=self._demo_drop_top+p.radius+8:
                return Controls(self._demo_drop_direction,0,True,False)
            self._demo_drop_direction=0
        if delta.y>50:
            # Walk off a supporting deck to descend. Jumping forever in the
            # same column only throws the sword back into that deck.
            supports=[w for w in world.geometry if type(w) is Cover and w.health>0 and w.blocks_body(p)
                      and abs(p.pos.y+p.radius-w.rect.top)<3 and w.rect.left-p.radius<p.pos.x<w.rect.right+p.radius]
            if supports:
                deck=max(supports,key=lambda w:w.rect.top)
                left=p.pos.x-(deck.rect.left-p.radius-8)
                right=deck.rect.right+p.radius+8-p.pos.x
                self._demo_drop_direction=-1 if left<right else 1
                self._demo_drop_top=deck.rect.top
                return Controls(self._demo_drop_direction,0,True,False)
            return Controls((delta.x>25)-(delta.x< -25),0,True,False)
        vector = normalized(delta)
        special = int(world.time * 3) % 11 == 0
        return Controls(vector.x if delta.length() > 180 else -vector.x, -1 if world.time % 1.2 < .15 else 0, True, special)


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
