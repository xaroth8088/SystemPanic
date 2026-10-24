"""Deterministic arcade simulation, independent of menus, rendering and audio."""
from __future__ import annotations

import math
import random
from typing import Callable, Literal, overload

from pygame.rect import Rect

from .model import (WIDTH, HEIGHT, FIXED_DT, Vec, Controls, Pilot, Enemy,
                    Body, Motion, Particle, normalized, unit, circle_rect)
from .paks import get_catalog, CHANNELS
from .preferences import Preferences
from .pak_api import ComponentBase, PilotBase, EnemyBase, WeaponBase, MusicBase, BackgroundBase, ObstaclesBase, ProjectileBase, EffectBase

SWAP_GLITCH_SECONDS = .25
LEVEL_CLEAR_SECONDS = 1.0
EnemyFactory = Callable[["World", int, Vec], Enemy]


class World:
    def __init__(self, prefs: Preferences, seed: int = 0, solo: str | None = None, catalog=None, audio=None):
        self.catalog = catalog if catalog is not None else get_catalog()
        self.prefs = Preferences.from_dict(vars(prefs), self.catalog)
        if solo is not None and solo not in self.catalog.complete_ids():
            raise ValueError("Solo play requires an installed complete Pak")
        self.solo = solo
        self.enabled = [self.solo] if self.solo else self.prefs.enabled.copy()
        missing = self.catalog.missing(self.enabled)
        if missing:
            raise ValueError("The installed mix is missing: " + ", ".join(missing))
        self.seed = seed
        self.rng = random.Random(seed)
        self._player: Pilot | None = None
        self.enemies: list[Enemy] = []
        self.projectiles: list[ProjectileBase] = []
        self.cover = []
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

    @property
    def factor(self):
        return {"relaxed": .70, "standard": 1., "intense": 1.28}[self.prefs.difficulty]

    @property
    def can_shuffle(self):
        if self.solo:
            return False
        if self.prefs.mix_mode == "coherent":
            return len(self.catalog.complete_ids(self.enabled)) > 1
        return any(len(self.catalog.providers(channel, self.enabled)) > 1 for channel in self.prefs.shuffle_channels)

    def choose(self, channel=None, previous=None):
        eligible = self.catalog.providers(channel, self.enabled) if channel else self.catalog.complete_ids(self.enabled)
        choices = [p for p in eligible if p != previous] or eligible
        return self.rng.choice(choices)

    def shuffle(self, initial=False):
        old_mix = self.mix.copy()
        if self.solo or self.prefs.mix_mode == "coherent":
            selected = self.solo or self.choose(previous=self.mix.get("pilot"))
            self.mix = {channel: selected for channel in CHANNELS}
        else:
            for channel in CHANNELS:
                if initial or channel in self.prefs.shuffle_channels:
                    self.mix[channel] = self.choose(channel, self.mix.get(channel))
        self.component("pilot")
        if old_mix.get("obstacles") != self.mix["obstacles"]:
            self.cover = self.component("obstacles").build()
        for channel in CHANNELS:
            self.component(channel)
        self.player.pos = self.safe_position(self.player.pos, self.player.radius + 2)
        self.player.invulnerable = max(1.5, self.player.invulnerable)
        if old_mix.get("enemy") != self.mix["enemy"]:
            adopted = []
            for old in self.enemies:
                enemy = self._make_enemy(old.id, old.pos)
                enemy.health, enemy.max_health = old.health, old.max_health
                enemy.pos = self.safe_position(enemy.pos, enemy.radius)
                adopted.append(enemy)
            self.enemies = adopted
        elif old_mix.get("obstacles") != self.mix["obstacles"]:
            for enemy in self.enemies:
                enemy.pos = self.safe_position(enemy.pos, enemy.radius)
        # Clear both teams' shots: the new rules begin from a readable state.
        self.projectiles.clear()
        self.shuffle_timer = float(self.prefs.shuffle_seconds)
        if not initial:
            self.shuffle_count += 1
            self.transition = SWAP_GLITCH_SECONDS
            self.suspend()
            self.events.append("shuffle")

    def safe_position(self, desired, radius: float = 14., avoid_player=False):
        def valid(pos):
            return (radius <= pos.x <= WIDTH - radius and radius <= pos.y <= HEIGHT - radius
                    and not any(circle_rect(pos, radius + 2, wall.rect) for wall in self.cover)
                    and (not avoid_player or pos.distance_to(self.player.pos) > 160))
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
        self.cover = [wall for wall in self.cover if not circle_rect(pos, radius + 3, wall.rect)]
        return pos

    def start_wave(self):
        self.wave += 1
        self.projectiles.clear()
        self.player.health = min(self.player.max_health, self.player.health + (0 if self.wave == 1 else 15))
        self.player.invulnerable = 2.
        count = self.wave
        for _ in range(count):
            pos = self.safe_position(Vec(self.rng.uniform(25, WIDTH - 25),
                                         self.rng.uniform(25, HEIGHT - 25)), avoid_player=True)
            self.spawn_enemy(pos)
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
        enemy.pos = self.safe_position(enemy.pos, enemy.radius)
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
        for enemy in tuple(self.enemies):
            if enemy.health > 0 and enemy.pos.distance_to(player.pos) < enemy.radius + player.radius:
                self.component("pilot").on_contact(self, enemy, dt)
                if enemy.health > 0:
                    self.component("enemy").on_contact(self, enemy, dt)
        self.remove_dead()
        if player.health <= 0:
            self.phase = "dead"
            self.suspend()
            self.burst(player.pos, self.pak("pilot").color, 35)
        elif not self.enemies:
            self.phase = "clear"
            self.phase_timer = LEVEL_CLEAR_SECONDS
            self.suspend()
            self.score += 250 * self.wave
            self.events.append("clear")

    def move_body(self, body, displacement, radius: float, *, bounds: Rect | None = Rect(0, 0, WIDTH, HEIGHT)) -> Motion:
        """Resolve geometry and return normals. The caller owns velocity/landing/wrap rules."""
        normals = []
        for axis in (0, 1):
            body.pos[axis] += displacement[axis]
            for wall in self.cover:
                if wall.health <= 0 or not circle_rect(body.pos, radius, wall.rect):
                    continue
                positive = displacement[axis] > 0
                normal = Vec()
                normal[axis] = -1 if positive else 1
                normals.append(normal)
                if axis == 0:
                    body.pos.x = wall.rect.left - radius if positive else wall.rect.right + radius
                else:
                    body.pos.y = wall.rect.top - radius if positive else wall.rect.bottom + radius
            if bounds is not None:
                low = bounds.left + radius if axis == 0 else bounds.top + radius
                high = bounds.right - radius if axis == 0 else bounds.bottom - radius
                if body.pos[axis] < low or body.pos[axis] > high:
                    normal = Vec()
                    normal[axis] = 1 if body.pos[axis] < low else -1
                    normals.append(normal)
                    body.pos[axis] = max(low, min(high, body.pos[axis]))
        return Motion(tuple(normals))

    def aim(self):
        if self.prefs.aim_assist and self.enemies:
            target = min(self.enemies, key=lambda e: e.pos.distance_squared_to(self.player.pos))
            return normalized(target.pos - self.player.pos)
        return unit(self.player.angle)

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
            self.component("enemy").on_death(self, enemy)

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
