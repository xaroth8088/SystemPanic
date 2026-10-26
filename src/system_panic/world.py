"""Deterministic arcade simulation, independent of menus, rendering and audio."""
from __future__ import annotations

import math
import random
from typing import Callable, Literal, overload

from pygame.rect import Rect

from .model import (WIDTH, HEIGHT, FIXED_DT, Vec, Controls, Pilot, Enemy,
                    Body, Motion, Particle, unit, circle_rect)
from .paks import get_catalog, CHANNELS
from .preferences import Preferences
from .remixes import validate_mix
from .pak_api import ComponentBase, PilotBase, EnemyBase, WeaponBase, MusicBase, BackgroundBase, ObstaclesBase, ProjectileBase, EffectBase, PowerupBase

SWAP_GLITCH_SECONDS = .25
LEVEL_CLEAR_SECONDS = 1.0
EnemyFactory = Callable[["World", int, Vec], Enemy]


class World:
    def __init__(self, prefs: Preferences, seed: int = 0, solo: str | None = None, catalog=None, audio=None,
                 *, fixed_mix: dict[str, str] | None = None):
        self.catalog = catalog if catalog is not None else get_catalog()
        self.prefs = Preferences.from_dict(vars(prefs), self.catalog)
        if solo is not None and fixed_mix is not None:
            raise ValueError("Choose either solo play or a fixed Remix")
        self.fixed_mix = validate_mix(fixed_mix, self.catalog) if fixed_mix is not None else None
        if solo is not None and solo not in self.catalog.complete_ids():
            raise ValueError("Solo play requires an installed complete Pak")
        self.solo = solo
        self.enabled = (list(dict.fromkeys(self.fixed_mix.values())) if self.fixed_mix is not None else
                        [self.solo] if self.solo else self.prefs.enabled.copy())
        missing = self.catalog.missing(self.enabled)
        if missing:
            raise ValueError("The installed mix is missing: " + ", ".join(missing))
        self.seed = seed
        self.rng = random.Random(seed)
        self._player: Pilot | None = None
        self.enemies: list[Enemy] = []
        self.projectiles: list[ProjectileBase] = []
        self.cover = []
        self._geometry = {}
        self.powerups: list[PowerupBase] = []
        self.powerups_collected = 0
        self.particles: list[Particle] = []
        self.effects: list[EffectBase] = []
        self.events: list[str] = []
        self.mix: dict[str, str] = {}
        self.audio = audio
        self._parts = {}
        self._part_sources = {}
        self.time = 0.
        self.wave = 0
        self.score = 0
        self.kills = 0
        self.next_id = 0
        self.shuffle_count = 0
        self.shuffle_timer = float(self.prefs.shuffle_seconds)
        self.transition = 0.
        self.phase = "ready"
        self.phase_timer = 1.6
        self.shake = 0.
        self._accumulator = 0.
        self.shuffle(initial=True)
        self.start_wave()

    def pak(self, channel):
        return self.catalog.by_id[self.mix[channel]]

    @property
    def player(self) -> Pilot:
        if self._player is None:
            raise RuntimeError("The pilot has not been created yet")
        return self._player

    @player.setter
    def player(self, body: Pilot):
        self._player = body

    @overload
    def component(self, channel: Literal["pilot"]) -> PilotBase: ...
    @overload
    def component(self, channel: Literal["enemy"]) -> EnemyBase: ...
    @overload
    def component(self, channel: Literal["weapon"]) -> WeaponBase: ...
    @overload
    def component(self, channel: Literal["music"]) -> MusicBase: ...
    @overload
    def component(self, channel: Literal["background"]) -> BackgroundBase: ...
    @overload
    def component(self, channel: Literal["obstacles"]) -> ObstaclesBase: ...
    @overload
    def component(self, channel: str) -> ComponentBase: ...
    def component(self, channel: str) -> ComponentBase:
        """Return the run-owned instance for this channel, never a catalog singleton."""
        if self._part_sources.get(channel) != self.mix[channel]:
            previous = self._parts.get(channel)
            if previous:
                previous.deactivate(self)
                previous.suspend()
                self.clear_geometry(previous)
            part = self.pak(channel).create(channel, self.audio)
            self._parts[channel] = part
            self._part_sources[channel] = self.mix[channel]
            if channel == "pilot":
                old = self._player
                position = old.pos.copy() if old else Vec(WIDTH / 2, HEIGHT / 2)
                self.player = part.create(self, position)
                if not isinstance(self.player, Pilot):
                    raise TypeError("PilotBase.create must return a Pilot body")
                if old:
                    self.player.health, self.player.max_health = old.health, old.max_health
                    self.player.invulnerable = old.invulnerable
            part.activate(self)
        return self._parts[channel]

    def suspend(self):
        for part in self._parts.values():
            part.suspend()

    def close(self):
        for part in self._parts.values():
            part.deactivate(self)
            part.suspend()
        self._parts.clear()
        self._part_sources.clear()
        self._geometry.clear()
        self.powerups.clear()

    @property
    def can_shuffle(self):
        if self.solo or self.fixed_mix is not None:
            return False
        if self.prefs.mix_mode == "coherent":
            return len(self.catalog.complete_ids(self.enabled)) > 1
        return any(len(self.catalog.providers(channel, self.enabled)) > 1 for channel in self.prefs.shuffle_channels)

    def choose(self, channel=None, previous=None):
        eligible = self.catalog.providers(channel, self.enabled) if channel else self.catalog.complete_ids(self.enabled)
        choices = [p for p in eligible if p != previous] or eligible
        return self.rng.choice(choices)

    def shuffle(self, initial=False):
        if self.fixed_mix is not None and not initial:
            return
        old_mix = self.mix.copy()
        if self.fixed_mix is not None:
            self.mix = self.fixed_mix.copy()
        elif self.solo or self.prefs.mix_mode == "coherent":
            selected = self.solo or self.choose(previous=self.mix.get("pilot"))
            self.mix = {channel: selected for channel in CHANNELS}
        else:
            for channel in CHANNELS:
                if initial or channel in self.prefs.shuffle_channels:
                    self.mix[channel] = self.choose(channel, self.mix.get(channel))
        self.component("pilot")
        if not initial and old_mix.get("obstacles") != self.mix["obstacles"]:
            self.cover = self.component("obstacles").build(self)
        for channel in CHANNELS:
            self.component(channel)
        self.player.pos = self.safe_position(self.player.pos, self.player.radius + 2)
        if old_mix.get("enemy") != self.mix["enemy"]:
            adopted = []
            for old in self.enemies:
                enemy = self._make_enemy(old.id, old.pos)
                enemy.health, enemy.max_health = old.health, old.max_health
                enemy.pos = self.safe_position(enemy.pos, enemy.radius, body=enemy)
                adopted.append(enemy)
            self.enemies = adopted
        elif old_mix.get("obstacles") != self.mix["obstacles"]:
            for enemy in self.enemies:
                enemy.pos = self.safe_position(enemy.pos, enemy.radius, body=enemy)
        # Scheduled objects cannot outlive the rules that created them across a swap.
        self.projectiles.clear()
        self.shuffle_timer = float(self.prefs.shuffle_seconds)
        if not initial:
            changed = frozenset(channel for channel in CHANNELS if old_mix.get(channel) != self.mix[channel])
            for channel in CHANNELS:
                self.component(channel).on_shuffle(self, changed)
            self.shuffle_count += 1
            self.transition = SWAP_GLITCH_SECONDS
            self.suspend()
            self.events.append("shuffle")

    def safe_position(self, desired, radius: float = 14., *, away_from: Vec | None = None, clearance: float = 0., body=None):
        def valid(pos):
            return (radius <= pos.x <= WIDTH - radius and radius <= pos.y <= HEIGHT - radius
                    and not any(wall.health > 0 and wall.blocks_body(body if body is not None else self._player) and wall.overlaps_circle(pos, radius + 2) for wall in self.geometry)
                    and (away_from is None or pos.distance_to(away_from) > clearance))
        pos = Vec(max(radius, min(WIDTH - radius, desired.x)),
                  max(radius, min(HEIGHT - radius, desired.y)))
        if valid(pos):
            return pos
        for distance in (24, 48, 80, 120, 180, 260, 360, 500):
            for index in range(16):
                candidate = pos + unit(index * math.tau / 16) * distance
                if valid(candidate):
                    return candidate
        for y in range(30, HEIGHT - 20, 40):
            for x in range(30, WIDTH - 20, 40):
                candidate = Vec(x, y)
                if valid(candidate):
                    return candidate
        # Bounded recovery for future unusually dense arenas.
        self.cover = [wall for wall in self.cover if not wall.overlaps_circle(pos, radius + 3)]
        return pos

    def start_wave(self):
        self.wave += 1
        self.projectiles.clear()
        self.cover = self.component("obstacles").build(self)
        self.player.pos = self.safe_position(self.player.pos, self.player.radius + 2)
        for channel in CHANNELS:
            self.component(channel).on_level_start(self)
        for _ in range(self.wave):
            self.spawn_enemy(self.component("enemy").spawn_position(self))
        # Only a new run has an introduction. Later levels resume directly
        # after their cleared message, without a second readiness pause.
        self.phase = "ready" if self.wave == 1 else "active"
        self.phase_timer = 1.5 if self.wave == 1 else 0.

    def _make_enemy(self, identity: int, position: Vec, factory: EnemyFactory | None = None) -> Enemy:
        factory = factory or self.component("enemy").create
        enemy = factory(self, identity, Vec(position))
        if not isinstance(enemy, Enemy) or enemy.id != identity:
            raise TypeError("Enemy factory must return an Enemy with the supplied identity")
        return enemy

    def spawn_enemy(self, position: Vec, *, factory: EnemyFactory | None = None) -> Enemy:
        """Register a Pak-created body; optional factories support arbitrary new entities."""
        self.next_id += 1
        enemy = self._make_enemy(self.next_id, position, factory)
        enemy.pos = self.safe_position(enemy.pos, enemy.radius, body=enemy)
        self.enemies.append(enemy)
        return enemy

    def advance(self, elapsed: float, controls: Controls):
        self._accumulator += max(0, min(.25, elapsed))
        while self._accumulator + 1e-10 >= FIXED_DT:
            self.step(FIXED_DT, controls)
            self._accumulator -= FIXED_DT

    def step(self, dt: float, controls: Controls):
        self.transition = max(0., self.transition - dt)
        self.shake = max(0., self.shake - dt * 20)
        self.update_effects(dt)
        if self.phase == "dead":
            return
        if self.phase != "active":
            self.phase_timer -= dt
            if self.phase_timer <= 0:
                if self.phase == "clear":
                    self.start_wave()
                else:
                    self.phase = "active"
            return
        # A short protected corruption transition; no simulation skips on slow frames.
        if self.transition > 0:
            return
        self.time += dt
        if self.can_shuffle:
            self.shuffle_timer -= dt
            if self.shuffle_timer <= 0:
                self.shuffle()
                return
        player = self.player
        for body in (player, *self.enemies):
            body.invulnerable = max(0., body.invulnerable - dt)
        self.component("pilot").update(self, dt, controls)
        self.component("weapon").update(self, dt, controls)
        self.update_enemies(dt)
        self.update_projectiles(dt)
        self.component("obstacles").update(self, dt)
        for pickup in tuple(self.powerups):
            if pickup.alive:
                pickup.update(self, dt)
        self.powerups = [pickup for pickup in self.powerups if pickup.alive]
        for enemy in tuple(self.enemies):
            if enemy.health > 0 and enemy.pos.distance_to(player.pos) < enemy.radius + player.radius:
                self.component("pilot").on_contact(self, enemy, dt)
                if enemy.health > 0:
                    self.component("enemy").on_contact(self, enemy, dt)
        self.remove_dead()
        if player.health <= 0:
            self.phase = "dead"
            self.component("pilot").on_death(self)
            self.suspend()
        elif not self.enemies:
            self.phase = "clear"
            self.phase_timer = LEVEL_CLEAR_SECONDS
            for channel in CHANNELS:
                self.component(channel).on_level_complete(self)
            self.suspend()
            self.events.append("clear")

    @property
    def geometry(self):
        if not self._geometry:
            return self.cover
        return self.cover + [wall for owner, walls in self._geometry.values() for wall in walls if wall.health > 0]

    def set_geometry(self, owner, walls):
        """Register component-owned shapes; replacement/close also release ownership."""
        self._geometry[id(owner)] = (owner, list(walls))

    def clear_geometry(self, owner):
        self._geometry.pop(id(owner), None)

    def segment_blocked(self, start, end, projectile=None):
        return any(w.health > 0 and w.blocks_projectile(projectile) and w.overlaps_segment(start, end) for w in self.geometry)

    def move_body(self, body, displacement, radius: float, *, bounds: Rect | None = Rect(0, 0, WIDTH, HEIGHT)) -> Motion:
        """Substepped shape queries prevent tunneling; callers own locomotion/response."""
        normals, notified = [], {}
        steps = max(1, math.ceil(max(abs(displacement.x), abs(displacement.y)) / max(2., min(8., radius / 2))))
        delta = displacement / steps
        geometry = self.geometry
        for _ in range(steps):
            for axis in (0, 1):
                amount = delta[axis]
                previous = body.pos.copy()
                if abs(amount) > 1e-12:
                    body.pos[axis] += amount
                    for wall in geometry:
                        if wall.health <= 0 or not wall.blocks_body(body) or not wall.overlaps_circle(body.pos, radius):
                            continue
                        normal = Vec()
                        normal[axis] = -1 if amount > 0 else 1
                        if not wall.overlaps_circle(previous, radius):
                            low, high = 0., 1.
                            for _ in range(12):
                                mid = (low + high) / 2
                                point = previous.copy()
                                point[axis] += amount * mid
                                if wall.overlaps_circle(point, radius): high = mid
                                else: low = mid
                            body.pos[axis] = previous[axis] + amount * low
                        else:
                            # Existing overlap can occur after a Pak's positional ability.
                            body.pos[axis] = previous[axis]
                        if id(wall) not in notified:
                            notified[id(wall)] = bool(wall.on_contact(self, body, normal))
                        if not notified[id(wall)]:
                            normals.append(normal)
                if bounds is not None:
                    low = bounds.left + radius if axis == 0 else bounds.top + radius
                    high = bounds.right - radius if axis == 0 else bounds.bottom - radius
                    if body.pos[axis] < low or body.pos[axis] > high:
                        normal = Vec()
                        normal[axis] = 1 if body.pos[axis] < low else -1
                        normals.append(normal)
                        body.pos[axis] = max(low, min(high, body.pos[axis]))
        return Motion(tuple(normals))

    def update_enemies(self, dt):
        for enemy in tuple(self.enemies):
            if enemy.health > 0:
                self.component("enemy").advance_enemy(self, enemy, dt)

    def update_projectiles(self, dt):
        for shot in tuple(self.projectiles):
            if shot.alive:
                shot.update(self, dt)
        self.projectiles = [shot for shot in self.projectiles if shot.alive]
        self.cover = [wall for wall in self.cover if wall.health > 0]

    def hit_enemy(self, enemy, damage):
        if enemy.health > 0:
            return self.component("enemy").take_damage(self, enemy, damage)
        return 0.

    def hit_player(self, damage):
        return self.component("pilot").take_damage(self, damage)

    def hit_cover(self, obstacle, damage):
        """Dispatch to the obstacle provider; durability is a Pak policy."""
        if obstacle.health > 0:
            return obstacle.damage(self, damage)
        return 0.

    @staticmethod
    def apply_damage(body: Body, damage: float) -> float:
        """A neutral primitive. Paks decide hit policy, effects and recovery windows."""
        if body.health <= 0 or body.invulnerable > 0:
            return 0.
        applied = min(body.health, max(0., damage))
        body.health -= applied
        return applied

    def remove_dead(self):
        dead = tuple(enemy for enemy in self.enemies if enemy.health <= 0)
        self.enemies = [enemy for enemy in self.enemies if enemy.health > 0]
        for enemy in dead:
            self.kills += 1
            position = enemy.pos.copy()
            if self.kills % 10 == 0:
                pickup = self.component("weapon").create_powerup(self, position)
                if pickup is not None:
                    if not isinstance(pickup, PowerupBase):
                        raise TypeError("WeaponBase.create_powerup must return a PowerupBase or None")
                    self.powerups.append(pickup)
            self.component("enemy").on_death(self, enemy)

    def collect_powerup(self, pickup):
        if not pickup.alive or not any(item is pickup for item in self.powerups):
            return False
        pickup.alive = False
        self.powerups_collected += 1
        self.component("weapon").on_powerup(self, self.powerups_collected)
        return True

    def burst(self, pos, color, count):
        # Derive presentation randomness without touching the gameplay RNG.
        for i in range(count):
            angle = (i * 2.39996 + self.time * 7) % math.tau
            life = .25 + (i % 5) * .08
            self.particles.append(Particle(Vec(pos), unit(angle) * (35 + i % 7 * 18),
                                            color, life, life, 2 + i % 3))
        self.particles = self.particles[-450:]

    def update_effects(self, dt):
        for particle in self.particles:
            particle.life -= dt
            particle.pos += particle.vel * dt
            particle.vel *= math.exp(-3 * dt)
        self.particles = [p for p in self.particles if p.life > 0]
        for effect in tuple(self.effects):
            if effect.alive:
                effect.update(dt)
        self.effects = [effect for effect in self.effects if effect.alive]

    def drain_events(self):
        events, self.events = self.events, []
        return events
