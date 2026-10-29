"""Hold to throw and reel a physical harpoon; release to snap its taut thread."""
import math
import pygame
from system_panic.model import Vec, normalized, unit, WIDTH, HEIGHT
from system_panic.pak_api import WeaponBase, ProjectileBase
from .powerup import Upgrade


def segment_distance(point, start, end):
    delta = end - start
    t = max(0., min(1., (point - start).dot(delta) / max(.0001, delta.length_squared())))
    return point.distance_to(start + delta * t)


class Loom(WeaponBase):
    def init(self):
        self.art = self.load_asset('weapon_sheet.png')
        self.sound = self.load_asset('shot.ogg')
        self.chime = self.load_asset('pickup.ogg')
        self.cooldown = 0.
        self.hook = None
        self.previous_fire = False

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0) * 9) % 4, columns=4)

    def create_powerup(self, world, position):
        return Upgrade(position, self.art, (151, 227, 255), self.chime)

    def on_powerup(self, world, count):
        world.burst(world.player.pos, (151, 227, 255), 12)

    def deactivate(self, world):
        if self.hook is not None:
            self.hook.alive = False
        self.hook = None

    def on_level_start(self, world):
        self.hook = None
        self.cooldown = 0.

    def update(self, world, dt, control):
        self.cooldown = max(0., self.cooldown - dt)
        if self.hook is not None and (not self.hook.alive or self.hook not in world.projectiles):
            self.hook = None
        if self.hook is not None:
            self.hook.reeling = bool(control.fire)
            if self.previous_fire and not control.fire:
                self.hook.snap(world)
                self.cooldown = .2
        if control.fire and self.hook is None and self.cooldown <= 0:
            intent = world.component('pilot').aim_direction(world)
            targets = [e for e in world.enemies if e.health > 0]
            if intent is not None:
                direction = normalized(intent)
            elif world.prefs.aim_assist and targets:
                target = min(targets, key=lambda e: e.pos.distance_squared_to(world.player.pos))
                direction = normalized(target.pos - world.player.pos)
            else:
                direction = unit(world.player.angle)
            self.hook = Thread(world.player.pos, direction, world.powerups_collected, self.art)
            world.projectiles.append(self.hook)
            self.sound.play(volume=.4)
            self.cooldown = .32
        self.previous_fire = bool(control.fire)

    def demo_controls(self, world, controls):
        # Actual held/release inputs; no direct calls to snap or target damage.
        controls.fire = world.time % 1.7 < 1.35
        return controls


class Thread(ProjectileBase):
    def __init__(self, position, direction, upgrades, art):
        super().__init__(position, direction * 640, 6)
        self.art = art
        self.age = self.latched = 0.
        self.upgrades = upgrades
        self.target = None
        self.reeling = True
        self.line_clock = 0.

    def update(self, world, dt):
        self.age += dt
        if self.age > 3.2 or self.pos.distance_to(world.player.pos) > 660:
            self.alive = False
            return
        if self.target is not None:
            if self.target not in world.enemies or self.target.health <= 0:
                self.alive = False
                return
            self.pos = self.target.pos.copy()
            self.latched += dt
            delta = world.player.pos - self.target.pos
            if world.segment_blocked(world.player.pos, self.target.pos, self):
                self.alive = False
                return
            if self.reeling:
                world.move_body(self.target, normalized(delta) * min(140, 65 + delta.length() * .3) * dt, self.target.radius)
                world.hit_enemy(self.target, (19 + self.upgrades * 2.5) * dt)
                self.line_clock -= dt
                if self.line_clock <= 0:
                    self.line_clock = .12
                    for enemy in world.enemies:
                        if enemy is not self.target and enemy.health > 0 and segment_distance(enemy.pos, world.player.pos, self.target.pos) < enemy.radius + 4:
                            world.hit_enemy(enemy, 8 + self.upgrades)
                if delta.length() < world.player.radius + self.target.radius + 36 or self.latched >= 1.4:
                    self.snap(world)
            return
        before = self.pos.copy()
        self.pos += self.vel * dt
        blockers = [wall for wall in world.geometry if wall.health > 0 and wall.blocks_projectile(self)
                    and wall.overlaps_segment(before, self.pos)]
        if blockers:
            first = min(blockers,key=lambda wall: Vec(wall.rect.center).distance_squared_to(before))
            world.hit_cover(first, 13 + self.upgrades * 2)
            self.alive = False
            return
        if not (0 <= self.pos.x <= WIDTH and 0 <= self.pos.y <= HEIGHT):
            self.alive = False
            return
        for enemy in world.enemies:
            if enemy.health > 0 and segment_distance(enemy.pos, before, self.pos) <= enemy.radius + self.radius:
                self.target = enemy
                self.pos = enemy.pos.copy()
                world.hit_enemy(enemy, 13 + self.upgrades * 2)
                world.burst(enemy.pos, (165, 239, 255), 5)
                break

    def snap(self, world):
        if not self.alive:
            return
        if self.target is not None and self.target in world.enemies and self.target.health > 0:
            # Release runs after pilot movement. Recheck the current span here,
            # before damage, even if yesterday's held-thread update was clear.
            if world.segment_blocked(world.player.pos, self.target.pos, self):
                self.alive = False
                return
            tension = min(1., self.latched / .8)
            damage = 14 + 30 * tension + self.upgrades * 4
            start, end = world.player.pos, self.target.pos
            for enemy in world.enemies:
                if enemy.health > 0 and segment_distance(enemy.pos, start, end) < enemy.radius + 9:
                    world.hit_enemy(enemy, damage)
                    world.move_body(enemy, normalized(enemy.pos - start) * (20 + tension * 25), enemy.radius)
            world.burst(end, (220, 247, 255), 13)
        self.alive = False

    def draw(self, graphics, surface, world):
        start = world.player.pos
        end = self.target.pos if self.target is not None and self.target in world.enemies else self.pos
        color = (226, 251, 255) if self.target is not None else (107, 194, 227)
        # The visible thread is the actual damaging/reeling span.
        pygame.draw.line(surface, (25, 73, 101), start, end, 5)
        pygame.draw.line(surface, color, start, end, 2)
        image = graphics.render_sprite(self.art.frame(int(self.age * 12) % 4, columns=4), 23, color)
        surface.blit(image, image.get_rect(center=end))
