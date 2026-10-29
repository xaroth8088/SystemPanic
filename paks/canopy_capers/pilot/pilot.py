"""A gravity-bound orchard courier. Stomp damage belongs entirely to the weapon."""
import math
import pygame
from system_panic.model import Pilot, Cover, Vec, Controls, WIDTH, HEIGHT
from system_panic.pak_api import PilotBase


class PilotComponent(PilotBase):
    controls = "Left / right: run. Primary / Up: double jump"
    special = "X: leaf glide"

    def init(self):
        self.art = self.load_asset("pilot_sheet.png")
        self.sound = self.load_asset("special.ogg")
        self.previous_fire = False
        self.previous_up = False
        self.previous_special = False
        self.jumps = 0
        self.grounded = False
        self.glide = 0.
        self.glide_cooldown = 0.
        self.depart = 0
        self.depart_top = 0.
        self.demo_waypoint = None

    def create(self, world, position):
        return Pilot(pos=Vec(position), radius=16, health=100, max_health=100)

    def sprite(self, world, entity=None):
        actor=entity if entity is not None else (world.player if world is not None else None)
        angle=actor.angle if actor is not None else 0.
        facing=0 if math.cos(angle)>=0 else 1
        phase=int((world.time if world is not None else 0)*8)%4
        return self.art.frame(phase*2+facing, columns=2, rows=4)

    def sprite_angle(self,world,entity):return 0.

    def sprite_flip_x(self,world,entity):return False


    def draw(self, graphics, surface, world, *, reduced_motion=False):
        p = world.player
        if p.invulnerable > 0:
            pygame.draw.circle(surface, world.pak("pilot").color, p.pos, 20, 1)
        if (world.phase != "active" or world.transition > 0 or p.invulnerable <= 0
                or int(world.time * 12) % 2 or reduced_motion):
            image = graphics.component_sprite(world, "pilot", p, 44)
            opaque = image.get_bounding_rect(min_alpha=110)
            offset = p.radius - (opaque.bottom - image.get_height() / 2)
            surface.blit(image, image.get_rect(center=p.pos + Vec(0, offset)))

    def on_level_start(self, world):
        self.previous_fire = False
        self.previous_up = False
        self.jumps = 0
        self.grounded = False
        if world.wave > 1:
            world.player.health = min(world.player.max_health, world.player.health + 15)
        world.player.invulnerable = max(world.player.invulnerable, 1.5)

    def on_shuffle(self, world, changed):
        world.player.invulnerable = max(world.player.invulnerable, 1.1)

    def update(self, world, dt, control):
        p = world.player
        self.glide = max(0., self.glide - dt)
        self.glide_cooldown = max(0., self.glide_cooldown - dt)
        up = control.y < -.5
        jump = (control.fire and not self.previous_fire) or (up and not self.previous_up)
        if jump and self.jumps < 2:
            p.vel.y = -430
            self.jumps += 1
            self.grounded = False
            world.burst(p.pos + Vec(0, 12), (160, 226, 103), 5)
        self.previous_fire, self.previous_up = bool(control.fire), up
        if control.special and not self.previous_special and self.glide_cooldown <= 0:
            self.glide, self.glide_cooldown = 1.05, 2.8
            self.sound.play(volume=.45)
        self.previous_special = control.special
        p.vel.x = control.x * (220 if self.glide else 245)
        p.vel.y = min(115 if self.glide else 580, p.vel.y + (260 if self.glide else 900) * dt)
        if control.x:
            p.angle = 0 if control.x > 0 else math.pi
        bounds = pygame.Rect(6, 6, WIDTH - 12, HEIGHT - 6)
        world.move_body(p, Vec(p.vel.x * dt, 0), p.radius, bounds=bounds)
        # Flat feet work with arbitrary rectangular covers via the public shape
        # query; one-way/spring decisions stay in the obstacle callbacks.
        delta = Vec(0, p.vel.y * dt)
        deck = None
        if p.vel.y >= 0:
            for wall in world.geometry:
                if getattr(wall.overlaps_circle, "__func__", None) is not Cover.overlaps_circle:
                    continue
                top = wall.rect.top - p.radius
                if (wall.health > 0 and wall.blocks_body(p)
                        and p.pos.y <= top <= p.pos.y + delta.y
                        and wall.rect.left - p.radius < p.pos.x < wall.rect.right + p.radius):
                    if deck is None or top < deck.rect.top - p.radius:
                        deck = wall
            if deck is not None:
                delta.y = deck.rect.top - p.radius - p.pos.y
        motion = world.move_body(p, delta, p.radius, bounds=bounds)
        landed = deck is not None and abs(p.pos.y + p.radius - deck.rect.top) < .01
        handled = bool(deck.on_contact(world, p, Vec(0, -1))) if landed else False
        if landed and deck is self.demo_waypoint:
            self.demo_waypoint = None
        if motion.blocked_y or (landed and not handled):
            p.vel.y = 0
        self.grounded = motion.landed or (landed and not handled)
        if self.grounded:
            self.jumps = 0

    def take_damage(self, world, damage):
        amount = world.apply_damage(world.player, damage)
        if amount:
            world.player.invulnerable = .85
            world.shake = 5
            world.events.append("hurt")
            world.burst(world.player.pos, (255, 150, 100), 9)
        return amount

    def on_death(self, world):
        world.burst(world.player.pos, (183, 235, 103), 26)

    def demo_controls(self, world):
        if not world.enemies:
            return Controls()
        p = world.player
        enemy = min(world.enemies, key=lambda e: e.pos.distance_squared_to(p.pos))
        target = enemy.pos + Vec(enemy.vel.x * .18, 0)
        waypoint = self.demo_waypoint
        if waypoint is not None:
            probe = Pilot(pos=Vec(waypoint.rect.centerx, waypoint.rect.top - p.radius - .05),
                          vel=Vec(0, 1), radius=p.radius)
            if (not any(wall is waypoint for wall in world.geometry) or waypoint.health <= 0
                    or not waypoint.blocks_body(probe)
                    or self.grounded and (abs(p.pos.y + p.radius - waypoint.rect.top) < 4
                                          or p.pos.y + p.radius - waypoint.rect.top > 185)):
                self.demo_waypoint = waypoint = None
        if waypoint is None and self.grounded and enemy.pos.y < p.pos.y - 100:
            candidates = []
            for wall in world.geometry:
                if wall.health <= 0 or getattr(wall.overlaps_circle, "__func__", None) is not Cover.overlaps_circle:
                    continue
                rise = p.pos.y + p.radius - wall.rect.top
                probe = Pilot(pos=Vec(wall.rect.centerx, wall.rect.top - p.radius - .05), vel=Vec(0, 1), radius=p.radius)
                if 25 < rise <= 185 and wall.rect.width > p.radius * 2 and wall.blocks_body(probe):
                    candidates.append(wall)
            if candidates:
                waypoint = min(candidates, key=lambda wall: abs(wall.rect.top - enemy.pos.y - enemy.radius)
                               + abs(wall.rect.centerx - enemy.pos.x) * .4 + abs(wall.rect.centerx - p.pos.x) * .15)
                self.demo_waypoint = waypoint
        if waypoint is not None:
            target = Vec(waypoint.rect.centerx, waypoint.rect.top - p.radius)
        dx = target.x - p.pos.x
        # Commit to walking off a supporting branch when the quarry is below.
        if self.depart:
            if p.pos.y < self.depart_top + p.radius + 10:
                return Controls(self.depart)
            self.depart = 0
        if enemy.pos.y > p.pos.y + 70:
            # Springs never report a grounded frame. Leave their column while
            # airborne too, instead of rebounding forever above a lower beetle.
            supports = [w for w in world.geometry if w.health > 0
                        and p.pos.y + p.radius - 4 <= w.rect.top < enemy.pos.y - enemy.radius
                        and w.rect.left - p.radius - 2 < p.pos.x < w.rect.right + p.radius + 2]
            if supports:
                wall = min(supports, key=lambda w: w.rect.top)
                self.depart = -1 if p.pos.x - wall.rect.left < wall.rect.right - p.pos.x else 1
                self.depart_top = wall.rect.top
                return Controls(self.depart)
        x = (dx > 9) - (dx < -9)
        jump = self.grounded and abs(dx) < 190
        # Extra jump helps climb a foreign cover; never bypass the input policy.
        if not self.grounded and target.y < p.pos.y + 25 and p.vel.y > -50 and self.jumps < 2:
            jump = True
        threat = enemy.pos - p.pos
        if abs(threat.x) < 70 and -40 < threat.y < 35 and not p.invulnerable:
            x = -1 if threat.x >= 0 else 1
            if self.grounded:
                jump = True
        return Controls(x, 0, jump and not self.previous_fire, False)
