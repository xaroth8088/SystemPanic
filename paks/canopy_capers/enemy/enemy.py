"""Lantern beetles hunt on the floor and hop between low branches."""
from dataclasses import dataclass, field
import math
import pygame
from system_panic.model import Enemy, Cover, Vec, WIDTH, HEIGHT
from system_panic.pak_api import EnemyBase
from .navigation import Navigator, GRAVITY, JUMP, AIR_SPEED, falling_time


@dataclass
class Beetle(Enemy):
    grounded: bool = False
    timer: float = 0.
    age: float = 0.
    touched: bool = False
    nav: object = None
    goal_key: int = -1
    flight: object = None
    air_x: float = 0.
    patrol_key: int = -1
    patrol_left: float = 0.
    next_patrol: float = 1.5
    drop_x: float | None = None
    drop_top: float = 0.
    blocked: dict = field(default_factory=dict)


class Enemies(EnemyBase):
    def init(self):
        self.art = self.load_asset("enemy_sheet.png")
        self.navigator = Navigator()

    def sprite(self, world, entity=None):
        actor=entity
        angle=actor.angle if actor is not None else 0.
        facing=0 if math.cos(angle)>=0 else 1
        phase=int((world.time if world is not None else 0)*8)%4
        return self.art.frame(phase*2+facing, columns=2, rows=4)

    def sprite_angle(self,world,entity):return 0.

    def sprite_flip_x(self,world,entity):return False


    def draw(self, graphics, surface, world, enemy, *, reduced_motion=False):
        image = graphics.component_sprite(world, "enemy", enemy, int(enemy.radius * 2.9), rotate=False)
        opaque = image.get_bounding_rect(min_alpha=110)
        offset = enemy.radius - (opaque.bottom - image.get_height() / 2)
        surface.blit(image, image.get_rect(center=enemy.pos + Vec(0, offset)))

    def spawn_position(self, world):
        probe = Enemy(id=world.next_id + 1, radius=14)
        surfaces = self.navigator.surfaces(world, probe)
        # Distribute actual starting bodies over independent public supports,
        # including the floor, instead of dropping every beetle onto the bottom.
        ordered = list(surfaces[1:]) + list(surfaces[:1])
        start = (world.next_id + world.wave) % len(ordered)
        for offset in range(len(ordered)):
            surface = ordered[(start + offset) % len(ordered)]
            x = surface.clamp(surface.center + world.rng.uniform(-25, 25))
            desired = Vec(x, surface.top - probe.radius - 3)
            if desired.distance_to(world.player.pos) < 115:
                continue
            probe.pos = desired.copy()
            return world.safe_position(desired, probe.radius, body=probe)
        desired = Vec(world.rng.uniform(35, WIDTH - 35), HEIGHT - 18)
        probe.pos = desired.copy()
        return world.safe_position(desired, probe.radius, away_from=world.player.pos, clearance=130, body=probe)

    def create(self, world, identity, position):
        health = 28 + 3.2 * world.wave
        return Beetle(id=identity, pos=Vec(position), radius=14, health=health, max_health=health,
                      timer=world.rng.uniform(.15, .45), next_patrol=.8 + identity % 5 * .3)

    def walk_speed(self, world):
        factor = {"relaxed": .7, "standard": 1., "intense": 1.25}[world.prefs.difficulty]
        return (112 + 38 * (1 - math.exp(-world.wave / 30))) * factor ** .5

    def steer(self, world, enemy, dt):
        surfaces = self.navigator.surfaces(world, enemy)
        available = {s.key: s for s in surfaces}
        source = self.navigator.supporting(enemy, surfaces) if enemy.grounded or enemy.touched else None
        if enemy.touched:
            enemy.flight = None
        enemy.touched = False
        enemy.blocked = {key: until for key, until in enemy.blocked.items() if until > enemy.age}
        enemy.patrol_left = max(0., enemy.patrol_left - dt)
        enemy.next_patrol -= dt
        if enemy.drop_x is not None:
            if enemy.pos.y + enemy.radius < enemy.drop_top + enemy.radius * 2 + 12:
                return math.copysign(self.walk_speed(world), enemy.drop_x - enemy.pos.x)
            enemy.drop_x = None
        if enemy.flight is not None:
            if enemy.flight.key not in available:
                enemy.flight = None
            else:
                duration = falling_time(enemy.pos.y + enemy.radius, enemy.vel.y, enemy.flight.top)
                if duration:
                    return max(-AIR_SPEED, min(AIR_SPEED, (enemy.air_x - enemy.pos.x) / duration))
                enemy.flight = None
        if source is None:
            return max(-160, min(160, (world.player.pos.x - enemy.pos.x) * 2))
        goal = self.navigator.goal(world.player, surfaces)
        if enemy.patrol_key == source.key:
            enemy.patrol_key = -1
            enemy.patrol_left = 0.
            enemy.next_patrol = 2.8 + enemy.id % 3 * .35
            enemy.timer = .25
        if goal.top < source.top - 30:
            enemy.patrol_key = -1
        if enemy.patrol_key not in available or enemy.patrol_left <= 0:
            enemy.patrol_key = -1
        if (source.key == 0 and goal.key == 0 and enemy.patrol_key < 0 and enemy.next_patrol <= 0
                and len(surfaces) > 1 and abs(world.player.pos.x - enemy.pos.x) > 80):
            elevated = surfaces[1:]
            choice = elevated[(enemy.id + int(enemy.age / 4)) % len(elevated)]
            if self.navigator.route(surfaces, source, choice, enemy.pos, enemy.blocked):
                enemy.patrol_key, enemy.patrol_left = choice.key, 8.
            else:
                enemy.next_patrol = 1.5
        if enemy.patrol_key in available:
            goal = available[enemy.patrol_key]
        speed = self.walk_speed(world)
        if goal.top > source.top + 30:
            enemy.nav = None
            # Walk off a real support before falling toward a lower quarry.
            # Springs use the same exit direction while automatically airborne.
            left, right = source.left - enemy.radius * 2 - 10, source.right + enemy.radius * 2 + 10
            exit_x = left if world.player.pos.x < enemy.pos.x else right
            if exit_x < 6 + enemy.radius:
                exit_x = right
            if exit_x > WIDTH - 6 - enemy.radius:
                exit_x = left
            enemy.drop_x, enemy.drop_top = exit_x, source.top
            return math.copysign(speed, exit_x - enemy.pos.x)
        if enemy.timer > 0:
            return 0.
        if source.key == goal.key:
            enemy.nav = None
            dx = goal.clamp(world.player.pos.x) - enemy.pos.x
            return (1 if dx > 8 else -1 if dx < -8 else 0) * speed
        if (enemy.nav is None or enemy.goal_key != goal.key or enemy.nav.source.key != source.key
                or enemy.nav.target.key not in available):
            enemy.nav, enemy.goal_key = None, goal.key
            leg = self.navigator.route(surfaces, source, goal, enemy.pos, enemy.blocked)
            if leg is not None:
                choices = sorted(self.navigator.alternatives(enemy, leg), key=lambda option: abs(option.launch_x - enemy.pos.x))
                enemy.nav = next((option for option in choices if self.navigator.clear_jump(world, enemy, option)), None)
                if enemy.nav is None:
                    enemy.blocked[(leg.source.key, leg.target.key)] = enemy.age + 1.
        leg = enemy.nav
        if leg is None:
            return 0.
        landing = leg.target.clamp(enemy.pos.x)
        if (abs(leg.launch_x - enemy.pos.x) > 4
                and abs(landing - enemy.pos.x) <= AIR_SPEED * leg.duration - 8):
            from .navigation import Leg
            immediate = Leg(leg.source, leg.target, enemy.pos.x, landing, leg.duration)
            if self.navigator.clear_jump(world, enemy, immediate):
                leg = enemy.nav = immediate
        dx = leg.launch_x - enemy.pos.x
        if abs(dx) > 4:
            return math.copysign(speed, dx)
        if enemy.grounded:
            enemy.vel.y = -JUMP
        # A spring has already supplied its own vertical velocity; retain it.
        duration = falling_time(enemy.pos.y + enemy.radius, enemy.vel.y, leg.target.top)
        if duration is None:
            return 0.
        enemy.flight, enemy.air_x = leg.target, leg.land_x
        enemy.nav, enemy.grounded = None, False
        return max(-AIR_SPEED, min(AIR_SPEED, (leg.land_x - enemy.pos.x) / duration))

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        enemy.vel.x = self.steer(world, enemy, dt)
        if abs(enemy.vel.x) > 1:
            enemy.angle = 0 if enemy.vel.x > 0 else math.pi
        enemy.vel.y = min(560, enemy.vel.y + GRAVITY * dt)
        bounds = pygame.Rect(6, 6, WIDTH - 12, HEIGHT - 6)
        world.move_body(enemy, Vec(enemy.vel.x * dt, 0), enemy.radius, bounds=bounds)
        deck = None
        displacement = Vec(0, enemy.vel.y * dt)
        if enemy.vel.y >= 0:
            for wall in world.geometry:
                if getattr(wall.overlaps_circle, "__func__", None) is not Cover.overlaps_circle:
                    continue
                top = wall.rect.top - enemy.radius
                if (wall.health > 0 and wall.blocks_body(enemy) and enemy.pos.y <= top <= enemy.pos.y + displacement.y
                        and wall.rect.left - enemy.radius < enemy.pos.x < wall.rect.right + enemy.radius):
                    if deck is None or wall.rect.top < deck.rect.top:
                        deck = wall
            if deck is not None:
                displacement.y = deck.rect.top - enemy.radius - enemy.pos.y
        motion = world.move_body(enemy, displacement, enemy.radius, bounds=bounds)
        landed = deck is not None and abs(enemy.pos.y + enemy.radius - deck.rect.top) < .01
        handled = bool(deck.on_contact(world, enemy, Vec(0, -1))) if landed else False
        if motion.blocked_y or (landed and not handled):
            enemy.vel.y = 0
        enemy.grounded = motion.landed or (landed and not handled)
        enemy.touched = motion.landed or landed

    def on_contact(self, world, enemy, dt):
        factor = {"relaxed": .7, "standard": 1., "intense": 1.25}[world.prefs.difficulty]
        world.hit_player((12 + world.wave ** .7 * .7) * factor)

    def on_death(self, world, enemy):
        world.score += 100
        world.burst(enemy.pos, (211, 178, 92), 10)
        world.events.append("impact")

    def on_level_complete(self, world):
        world.score += 250 * world.wave
