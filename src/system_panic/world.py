"""Deterministic arcade simulation, independent of menus, rendering and audio."""
from __future__ import annotations

from dataclasses import replace
import math
import random

import pygame

from .model import (WIDTH, HEIGHT, FIXED_DT, Vec, Controls, Pilot, Enemy,
                    Projectile, Particle, Beam, normalized, unit, circle_rect)
from .paks import BY_ID, CHANNELS
from .preferences import Preferences

SWAP_GLITCH_SECONDS = .25
LEVEL_CLEAR_SECONDS = 1.0


class World:
    def __init__(self, prefs: Preferences, seed: int = 0, solo: str | None = None):
        self.prefs = Preferences.from_dict(vars(prefs))
        self.solo = solo if solo in BY_ID else None
        self.enabled = [self.solo] if self.solo else self.prefs.enabled.copy()
        self.seed = seed
        self.rng = random.Random(seed)
        self.player = Pilot()
        self.enemies: list[Enemy] = []
        self.projectiles: list[Projectile] = []
        self.cover = []
        self.particles: list[Particle] = []
        self.beams: list[Beam] = []
        self.events: list[str] = []
        self.mix: dict[str, str] = {}
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
        self.previous_y = 0.
        self.previous_special = False
        self.shake = 0.
        self._accumulator = 0.
        self.shuffle(initial=True)
        self.start_wave()

    def pak(self, channel):
        return BY_ID[self.mix[channel]]

    @property
    def factor(self):
        return {"relaxed": .70, "standard": 1., "intense": 1.28}[self.prefs.difficulty]

    def choose(self, previous=None):
        choices = [p for p in self.enabled if p != previous] or self.enabled
        return self.rng.choice(choices)

    def shuffle(self, initial=False):
        old_pilot = self.mix.get("pilot")
        if len(self.enabled) == 1 or self.prefs.mix_mode == "coherent":
            selected = self.choose(self.mix.get("pilot"))
            self.mix = {channel: selected for channel in CHANNELS}
        else:
            for channel in CHANNELS:
                if initial or channel in self.prefs.shuffle_channels:
                    self.mix[channel] = self.choose(self.mix.get(channel))
        self.cover = self.pak("arena").make_arena()
        if old_pilot != self.mix["pilot"]:
            old = self.player
            self.player = Pilot(pos=old.pos.copy(), health=old.health,
                                invulnerable=max(old.invulnerable, 1.5), fire_timer=old.fire_timer)
            if self.pak("pilot").pilot == "orbiter":
                offset = old.pos - Vec(WIDTH / 2, HEIGHT / 2)
                self.player.angle = math.atan2(offset.y, offset.x)
                self.player.orbit_radius = max(80, min(215, offset.length()))
        self.player.pos = self.safe_position(self.player.pos, 13)
        self.player.invulnerable = max(1.5, self.player.invulnerable)
        family = self.pak("enemy").enemy
        self.enemies = [replace(enemy, family=family, pos=self.safe_position(enemy.pos, enemy.radius),
                                vel=Vec(), timer=self.rng.uniform(.6, 1.8), age=0,
                                angle=self.rng.uniform(0, math.tau)) for enemy in self.enemies]
        # Clear both teams' shots: the new rules begin from a readable state.
        self.projectiles.clear()
        self.shuffle_timer = float(self.prefs.shuffle_seconds)
        if not initial:
            self.shuffle_count += 1
            self.transition = SWAP_GLITCH_SECONDS
            self.events.append("shuffle")

    def safe_position(self, desired, radius=14, avoid_player=False):
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
        self.player.health = min(100, self.player.health + (0 if self.wave == 1 else 15))
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

    def spawn_enemy(self, pos, elite=False, size=0):
        self.next_id += 1
        health = (30 + self.wave * 3) * (2.8 if elite else 1) * (.50 if size else 1)
        self.enemies.append(Enemy(self.next_id, Vec(pos), self.pak("enemy").enemy,
                                  health, health, 23 if elite else 9 if size else 14,
                                  timer=self.rng.uniform(.6, 2),
                                  angle=self.rng.uniform(0, math.tau), size=size, elite=elite))

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
        if len(self.enabled) > 1 and (self.prefs.mix_mode == "coherent" or self.prefs.shuffle_channels):
            self.shuffle_timer -= dt
            if self.shuffle_timer <= 0:
                self.shuffle()
                return
        player = self.player
        player.invulnerable = max(0., player.invulnerable - dt)
        player.fire_timer = max(0., player.fire_timer - dt)
        player.special_timer = max(0., player.special_timer - dt)
        player.phase_timer = max(0., player.phase_timer - dt)
        jump = controls.y < -.5 and self.previous_y >= -.5
        special = controls.special and not self.previous_special and player.special_timer <= 0
        self.previous_y = controls.y
        self.previous_special = controls.special
        self.move_player(dt, controls, jump, special)
        if controls.fire and player.fire_timer <= 0:
            self.fire_weapon()
        self.update_enemies(dt)
        self.update_projectiles(dt)
        for enemy in self.enemies:
            if enemy.health > 0 and enemy.pos.distance_to(player.pos) < enemy.radius + 11:
                if player.phase_timer > 0:
                    self.damage_enemy(enemy, 140 * dt)
                else:
                    self.hurt_player(13 if not enemy.elite else 22)
        self.remove_dead()
        if player.health <= 0:
            self.phase = "dead"
            self.burst(player.pos, self.pak("pilot").color, 35)
        elif not self.enemies:
            self.phase = "clear"
            self.phase_timer = LEVEL_CLEAR_SECONDS
            self.score += 250 * self.wave
            self.events.append("clear")

    def move_player(self, dt, control, jump, special):
        if special:
            self.player.special_timer = 2.8
            self.player.invulnerable = max(self.player.invulnerable, .65)
            self.player.phase_timer = .45
            self.events.append("select")
        self.pak("pilot").move(self, dt, control, jump, special)

    def move_body(self, body, displacement, radius, wrap=False):
        old_y = body.pos.y
        for axis in (0, 1):
            body.pos[axis] += displacement[axis]
            for wall in self.cover:
                if wall.health <= 0 or not circle_rect(body.pos, radius, wall.rect):
                    continue
                if axis == 0:
                    body.pos.x = wall.rect.left - radius if displacement.x > 0 else wall.rect.right + radius
                else:
                    if displacement.y > 0:
                        body.pos.y = wall.rect.top - radius
                        if isinstance(body, Pilot):
                            body.grounded = True
                            body.jumps = 0
                    else:
                        body.pos.y = wall.rect.bottom + radius
                    body.vel.y = 0
            if wrap:
                body.pos[axis] %= WIDTH if axis == 0 else HEIGHT
            else:
                limit = WIDTH if axis == 0 else HEIGHT
                margin = 22 if isinstance(body, Pilot) else radius
                if body.pos[axis] > limit - margin or body.pos[axis] < margin:
                    body.pos[axis] = max(margin, min(limit - margin, body.pos[axis]))
                    if axis == 1:
                        body.vel.y = 0
                        if isinstance(body, Pilot) and old_y <= body.pos.y:
                            body.grounded = True
                            body.jumps = 0

    def aim(self):
        if self.prefs.aim_assist and self.enemies:
            target = min(self.enemies, key=lambda e: e.pos.distance_squared_to(self.player.pos))
            return normalized(target.pos - self.player.pos)
        return unit(self.player.angle)

    def fire_weapon(self):
        self.player.fire_timer = self.pak("weapon").cooldown
        self.events.append("shot")
        self.pak("weapon").fire(self, self.aim())

    def spawn_shot(self, direction, kind, damage, speed, radius=4, pierce=0,
                   bounce=0, homing=0., blast=0., return_after=-1.):
        self.projectiles.append(Projectile(self.player.pos + direction * 19,
            direction * speed, kind, damage, 3., radius=radius, pierce=pierce,
            bounce=bounce, homing=homing, blast=blast, return_after=return_after))

    def update_enemies(self, dt):
        for enemy in self.enemies:
            if enemy.health > 0:
                enemy.age += dt
                enemy.timer -= dt
                self.pak("enemy").advance_enemy(self, enemy, dt)

    def enemy_shot(self, enemy, direction, speed):
        self.projectiles.append(Projectile(enemy.pos + direction * (enemy.radius + 6),
                                            direction * speed, "hostile", 12, 7,
                                            friendly=False, radius=5))

    def update_projectiles(self, dt):
        for shot in self.projectiles:
            if shot.life <= 0:
                continue
            shot.life -= dt
            shot.age += dt
            if shot.return_after >= 0 and shot.age > shot.return_after:
                shot.vel = normalized(self.player.pos - shot.pos) * 490
                if shot.pos.distance_to(self.player.pos) < 16:
                    shot.life = 0
                    continue
            # Mild seeking keeps long-range weapons viable with every locomotion model.
            if shot.homing > 0 and self.prefs.aim_assist and self.enemies:
                target = min(self.enemies, key=lambda e: e.pos.distance_squared_to(shot.pos))
                desired = normalized(target.pos - shot.pos) * 380
                shot.vel = shot.vel.lerp(desired, min(1, dt * shot.homing))
            shot.pos += shot.vel * dt
            if not (4 <= shot.pos.x <= WIDTH - 4 and 4 <= shot.pos.y <= HEIGHT - 4):
                if shot.bounce > 0:
                    if shot.pos.x < 4 or shot.pos.x > WIDTH - 4:
                        shot.vel.x *= -1
                    if shot.pos.y < 4 or shot.pos.y > HEIGHT - 4:
                        shot.vel.y *= -1
                    shot.bounce -= 1
                    shot.pos.x = max(4, min(WIDTH - 4, shot.pos.x))
                    shot.pos.y = max(4, min(HEIGHT - 4, shot.pos.y))
                else:
                    shot.life = 0
            for wall in self.cover:
                if wall.health <= 0 or not circle_rect(shot.pos, shot.radius, wall.rect):
                    continue
                if shot.friendly:
                    wall.health -= shot.damage
                if shot.bounce > 0:
                    # Back out to prevent spending every bounce inside the same cover.
                    shot.pos -= shot.vel * dt * 2
                    shot.vel *= -1
                    shot.bounce -= 1
                else:
                    if shot.blast > 0:
                        self.explode(shot)
                    shot.life = 0
                break
            if shot.life <= 0:
                continue
            if shot.friendly:
                for enemy in self.enemies:
                    if enemy.health <= 0 or enemy.id in shot.hit_ids:
                        continue
                    if enemy.pos.distance_to(shot.pos) < enemy.radius + shot.radius:
                        self.damage_enemy(enemy, shot.damage)
                        shot.hit_ids.add(enemy.id)
                        if shot.blast > 0:
                            self.explode(shot)
                        if shot.pierce:
                            shot.pierce -= 1
                        else:
                            shot.life = 0
                            break
            elif shot.pos.distance_to(self.player.pos) < 12 + shot.radius:
                self.hurt_player(shot.damage)
                shot.life = 0
        self.projectiles = [shot for shot in self.projectiles if shot.life > 0]
        self.cover = [wall for wall in self.cover if wall.health > 0]

    def explode(self, shot):
        for enemy in self.enemies:
            if enemy.health > 0 and enemy.pos.distance_to(shot.pos) < shot.blast + enemy.radius:
                self.damage_enemy(enemy, shot.damage * .7)
        for wall in self.cover:
            if circle_rect(shot.pos, shot.blast, wall.rect):
                wall.health -= shot.damage
        self.burst(shot.pos, self.pak("weapon").color, 20)
        self.shake = max(self.shake, 3)

    def damage_enemy(self, enemy, damage):
        if enemy.health <= 0:
            return
        enemy.health -= damage
        self.burst(enemy.pos, self.pak("enemy").color, 2)

    def hurt_player(self, damage):
        if self.player.invulnerable > 0:
            return
        self.player.health = max(0., self.player.health - damage * self.factor)
        self.player.invulnerable = .9
        self.shake = 6
        self.events.append("hurt")
        self.burst(self.player.pos, (255, 110, 130), 14)

    def remove_dead(self):
        children = []
        for enemy in self.enemies:
            if enemy.health > 0:
                continue
            self.kills += 1
            self.score += 150 if enemy.elite else 60 if enemy.size else 100
            self.burst(enemy.pos, self.pak("enemy").color, 15 if enemy.elite else 9)
            self.events.append("impact")
            if self.pak("enemy").splits and not enemy.size:
                for index in range(self.pak("enemy").splits):
                    offset = -18 + index * 36
                    children.append(self.safe_position(enemy.pos + Vec(offset, offset), 9))
        self.enemies = [enemy for enemy in self.enemies if enemy.health > 0]
        for pos in children:
            self.spawn_enemy(pos, size=1)

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
        for beam in self.beams:
            beam.life -= dt
        self.beams = [b for b in self.beams if b.life > 0]

    def drain_events(self):
        events, self.events = self.events, []
        return events
