"""Level-based Pak difficulty and repeatable, regenerating procedural geometry."""
import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from system_panic.model import Vec, Controls, WIDTH, HEIGHT, FIXED_DT, circle_rect
from system_panic.paks import get_catalog
from system_panic.preferences import Preferences
from system_panic.world import World

PAKS = get_catalog().complete_ids()


def layout(obstacles):
    return tuple(tuple(obstacle.rect) for obstacle in obstacles)


class LevelTests(unittest.TestCase):
    def test_every_pak_scales_health_damage_and_movement_or_attack_speed(self):
        for pak in PAKS:
            with self.subTest(pak=pak):
                world = World(Preferences(), 24, solo=pak)
                part = world.component("enemy")
                speed = getattr(part, "move_speed", None) or getattr(part, "shot_speed")
                samples = []
                for level in (1, 12, 50, 101):
                    world.wave = level
                    enemy = part.create(world, 1000, Vec(100, 100))
                    samples.append((enemy.max_health, part.contact_damage(world), speed(world)))
                for before, after in zip(samples, samples[1:]):
                    self.assertTrue(all(b > a for a, b in zip(before, after)), samples)
                for field in ("fire_interval", "dash_interval", "teleport_interval"):
                    if hasattr(part, field):
                        interval = getattr(part, field)
                        world.wave = 1
                        first = interval(world)
                        world.wave = 30
                        self.assertLess(interval(world), first)
                        self.assertGreater(interval(world), .1)
                world.wave = 12
                damage = []
                for preference in ("relaxed", "standard", "intense"):
                    world.prefs.difficulty = preference
                    damage.append(part.contact_damage(world))
                self.assertLess(damage[0], damage[1])
                self.assertLess(damage[1], damage[2])

    def test_later_turrets_lead_moving_targets_and_alternate_fan_volleys(self):
        world = World(Preferences(), 24, solo="iron_circuit")
        world.cover = []
        world.player.pos, world.player.vel = Vec(700, 220), Vec(0, 100)
        part = world.component("enemy")
        directions = []
        low_damage = 0.
        for level in (1, 12):
            world.wave, world.projectiles = level, []
            enemy = part.create(world, 1, Vec(200, 220))
            enemy.timer = 0
            part.advance_enemy(world, enemy, FIXED_DT)
            directions.append(world.projectiles[0].vel.normalize())
            self.assertEqual(len(world.projectiles), 1)
            first_damage = world.projectiles[0]._damage
            enemy.timer = 0
            part.advance_enemy(world, enemy, FIXED_DT)
            self.assertEqual(len(world.projectiles), 4 if level >= 8 else 2)
            if level == 1:
                low_damage = first_damage
            else:
                self.assertGreater(first_damage, low_damage)
        self.assertAlmostEqual(directions[0].y, 0)
        self.assertGreater(directions[1].y, .02)

    def test_later_swarms_intercept_and_phantoms_reaim_after_teleporting(self):
        world = World(Preferences(), 24, solo="signal_runner")
        world.cover = []
        world.player.pos, world.player.vel = Vec(700, 220), Vec(0, 200)
        part = world.component("enemy")
        velocities = []
        for level in (1, 20):
            world.wave = level
            enemy = part.create(world, 2, Vec(200, 220))
            part.advance_enemy(world, enemy, FIXED_DT)
            velocities.append(enemy.vel.normalize())
        self.assertNotAlmostEqual(velocities[0].y, velocities[1].y, places=2)
        world = World(Preferences(), 24, solo="phase_garden")
        world.wave, world.cover = 20, []
        world.player.vel = Vec()
        enemy = world.enemies[0]
        enemy.timer = 0
        world.component("enemy").advance_enemy(world, enemy, FIXED_DT)
        shot = world.projectiles[0]
        toward = (world.player.pos - enemy.pos).normalize()
        self.assertGreater(shot.vel.normalize().dot(toward), .999)
        self.assertGreaterEqual(enemy.pos.distance_to(world.player.pos), 100)

    def test_layouts_vary_by_level_and_seed_without_consuming_combat_rng(self):
        for pak in PAKS:
            with self.subTest(pak=pak):
                signatures = []
                for seed in (0, 3, 24, 101):
                    world = World(Preferences(), seed, solo=pak)
                    part = world.component("obstacles")
                    for level in (1, 2, 7, 12, 101):
                        world.wave = level
                        before = world.rng.getstate()
                        first, second = part.build(world), part.build(world)
                        self.assertEqual(before, world.rng.getstate())
                        self.assertEqual(layout(first), layout(second))
                        self.assertIsNot(first[0], second[0])
                        signatures.append(layout(first))
                        for obstacle in first:
                            rect = obstacle.rect
                            self.assertTrue(0 < rect.left < rect.right < WIDTH)
                            self.assertTrue(0 < rect.top < rect.bottom < HEIGHT)
                            self.assertEqual(obstacle.health, obstacle.max_health)
                        self.assertFalse(any(a.rect.colliderect(b.rect) for i, a in enumerate(first) for b in first[i + 1:]))
                self.assertEqual(len(set(signatures)), len(signatures))

    def test_level_clear_rebuilds_destroyed_obstacles_in_solo_and_locked_mixes(self):
        for pak in PAKS:
            for solo in (pak, None):
                with self.subTest(pak=pak, solo=solo):
                    world = World(Preferences(shuffle_channels=["music"]), 24, solo=solo)
                    if not solo:
                        world.mix["obstacles"] = pak
                        world.cover = world.component("obstacles").build(world)
                    part = world.component("obstacles")
                    calls = []
                    original = part.build
                    def recorded(w):
                        calls.append(w.wave)
                        return original(w)
                    part.build = recorded
                    old, signature = world.cover.copy(), layout(world.cover)
                    for obstacle in old:
                        obstacle.health = 0
                    world.cover.clear()
                    world.enemies.clear()
                    world.phase = "active"
                    world.step(FIXED_DT, Controls())
                    self.assertEqual(world.phase, "clear")
                    self.assertFalse(world.cover)  # Rebuild at arrival, after the clear message.
                    for _ in range(121):
                        world.step(FIXED_DT, Controls())
                    self.assertEqual((world.wave, world.phase, world.transition), (2, "active", 0))
                    self.assertEqual(calls, [2])
                    self.assertIs(world.component("obstacles"), part)
                    self.assertNotEqual(layout(world.cover), signature)
                    self.assertTrue(all(c.health == c.max_health > 0 for c in world.cover))
                    self.assertTrue(all(c is not old_c for c in world.cover for old_c in old))
                    self.assertEqual(len(world.enemies), 2)
                    for body in (world.player, *world.enemies):
                        self.assertFalse(any(circle_rect(body.pos, body.radius, c.rect) for c in world.cover))

    def test_unrelated_shuffle_preserves_layout_and_damage_but_level_change_does_not(self):
        world = World(Preferences(shuffle_channels=["music", "background"]), 24)
        part, walls = world.component("obstacles"), world.cover
        walls[0].health = 7
        signature = layout(walls)
        world.shuffle()
        self.assertIs(world.cover, walls)
        self.assertEqual(layout(world.cover), signature)
        self.assertEqual(walls[0].health, 7)
        world.enemies.clear()
        world.start_wave()
        self.assertIs(world.component("obstacles"), part)
        self.assertIsNot(world.cover, walls)
        self.assertNotEqual(layout(world.cover), signature)
