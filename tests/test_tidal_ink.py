"""Tidal enemy hazards: visible damage footprint, unchanged timing and pure drawing."""
import importlib
import hashlib
import math
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pygame
from system_panic.graphics import Graphics
from system_panic.model import Vec
from system_panic.preferences import Preferences
from system_panic.world import World


class TidalInkTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((1, 1))
        self.world = World(Preferences(), 24, solo="tidal_choir")
        self.world.cover = []
        self.hazards = importlib.import_module(type(self.world.component("enemy")).__module__ + ".hazards")
        self.graphics = Graphics(self.world.catalog)
        self.surface = pygame.Surface((960, 480), pygame.SRCALPHA)

    def tearDown(self):
        self.world.close()
        pygame.quit()

    def test_cloud_fills_the_active_damage_area_and_stays_hidden_before_activation(self):
        cloud = self.hazards.Zone(Vec(400, 240), 55, .6, 12, .8)
        for age in (0., .59):
            cloud.age = age
            cloud.draw(None, self.surface, self.world)
            self.assertEqual(self.surface.get_bounding_rect().width, 0)
        cloud.age = .6
        cloud.draw(None, self.surface, self.world)
        self.assertGreater(pygame.mask.from_surface(self.surface, threshold=0).count(), math.pi * 55**2 * .85)
        self.assertGreater(self.surface.get_at((424, 251)).a, 0)
        self.assertEqual(self.surface.get_at((457, 240)).a, 0)
        self.surface.fill((0, 0, 0, 0))
        cloud.update(self.world, .801)
        self.assertFalse(cloud.alive)
        cloud.draw(None, self.surface, self.world)
        self.assertEqual(self.surface.get_bounding_rect().width, 0)

    def test_level_five_charge_leaves_the_original_ink_damage_schedule(self):
        w = self.world
        enemy = w.enemies[0]
        for level in (4, 5):
            w.wave = level
            w.projectiles.clear()
            enemy.pos, enemy.vel = Vec(300, 200), Vec()
            enemy.state, enemy.timer, enemy.target = "windup", 0., Vec(650, 200)
            origin = enemy.pos.copy()
            w.component("enemy").advance_enemy(w, enemy, .01)
            self.assertEqual(enemy.state, "charge")
            self.assertAlmostEqual(enemy.vel.length(), 300.)
            self.assertEqual(len(w.projectiles), int(level >= 5))
        cloud = w.projectiles[0]
        self.assertEqual(cloud.pos, origin)
        self.assertEqual((cloud.radius, cloud.delay, cloud.duration), (55, .6, .8))
        self.assertEqual(cloud.damage, w.component("enemy").contact_damage(w))
        w.player.pos = origin.copy()
        with patch.object(w, "hit_player") as hit:
            cloud.update(w, .59)
            hit.assert_not_called()
            cloud.update(w, .01)
            hit.assert_called_once_with(cloud.damage)
            hit.reset_mock()
            w.player.pos = origin + Vec(55 + w.player.radius + 1, 0)
            cloud.update(w, .1)
            hit.assert_not_called()
            cloud.update(w, .701)
            self.assertFalse(cloud.alive)

    def test_rendering_is_pure_reduced_motion_is_steady_and_wake_only_follows_charge(self):
        w = self.world
        cloud = self.hazards.Zone(Vec(400, 240), 55, .6, 12, .8)
        snapshots = []
        for reduced in (False, True):
            w.prefs.reduced_motion = reduced
            frames = []
            for age in (.6, 1.):
                cloud.age = age
                before = (w.rng.getstate(), w.time, cloud.pos.copy(), cloud.age, cloud.alive)
                self.surface.fill((0, 0, 0, 0))
                cloud.draw(None, self.surface, w)
                frames.append(hashlib.sha256(pygame.image.tobytes(self.surface, "RGBA")).digest())
                self.assertEqual((w.rng.getstate(), w.time, cloud.pos, cloud.age, cloud.alive), before)
            snapshots.append(frames)
        self.assertNotEqual(*snapshots[0])
        self.assertEqual(*snapshots[1])
        enemy = w.enemies[0]
        enemy.pos, enemy.vel = Vec(500, 240), Vec(300, 0)
        frames = []
        for state in ("seek", "windup", "charge"):
            enemy.state = state
            before = (w.rng.getstate(), enemy.pos.copy(), enemy.vel.copy(), enemy.state, enemy.age)
            self.surface.fill((0, 0, 0, 0))
            w.component("enemy").draw(self.graphics, self.surface, w, enemy, reduced_motion=True)
            frames.append(hashlib.sha256(pygame.image.tobytes(self.surface, "RGBA")).digest())
            self.assertEqual((w.rng.getstate(), enemy.pos, enemy.vel, enemy.state, enemy.age), before)
        self.assertEqual(frames[0], frames[1])
        self.assertNotEqual(frames[1], frames[2])
