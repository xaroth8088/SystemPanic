import itertools
import math
import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from system_panic.model import Controls, Vec, FIXED_DT, circle_rect, WIDTH, HEIGHT
from system_panic.pak_api import ProjectileBase
from system_panic.paks import get_catalog, CHANNELS, GAMEPLAY_CHANNELS
PAKS = get_catalog().paks
from system_panic.preferences import Preferences
from system_panic.world import World, SWAP_GLITCH_SECONDS, LEVEL_CLEAR_SECONDS


class CountingShot(ProjectileBase):
    def update(self, world, dt):
        self.pos += self.vel * dt

    def draw(self, graphics, surface, world):
        pass


class WorldTests(unittest.TestCase):
    def test_periodic_swap_only_freezes_during_glitch_then_accepts_held_input(self):
        for mode in ("coherent", "remix"):
            with self.subTest(mode=mode):
                world = World(Preferences(enabled=["signal_runner", "phase_garden"], mix_mode=mode), seed=9)
                world.phase = "active"
                world.shuffle_timer = FIXED_DT / 2
                held = Controls(x=1, fire=True)
                world.step(FIXED_DT, held)
                self.assertEqual(world.shuffle_count, 1)
                self.assertEqual(world.phase, "active")
                self.assertAlmostEqual(world.transition, SWAP_GLITCH_SECONDS)
                position, time = world.player.pos.copy(), world.time
                enemies = [enemy.pos.copy() for enemy in world.enemies]
                while world.transition > FIXED_DT + 1e-9:
                    world.step(FIXED_DT, held)
                    self.assertEqual(world.player.pos, position)
                    self.assertEqual([enemy.pos for enemy in world.enemies], enemies)
                    self.assertEqual(world.time, time)
                    self.assertEqual(world.phase, "active")
                world.advance(FIXED_DT * 2, held)
                self.assertEqual(world.phase, "active")
                self.assertEqual(world.wave, 1)
                self.assertGreater(world.time, time)
                self.assertNotEqual(world.player.pos, position)
                self.assertTrue(world.projectiles or world.effects)

    def test_level_clear_has_its_own_message_delay_then_direct_action(self):
        world = World(Preferences(), seed=24, solo="signal_runner")
        world.phase = "active"
        world.player.health = 50
        for enemy in world.enemies:
            enemy.health = 0
        world.step(FIXED_DT, Controls())
        self.assertEqual(world.phase, "clear")
        self.assertAlmostEqual(world.phase_timer, LEVEL_CLEAR_SECONDS)
        position, time, mix = world.player.pos.copy(), world.time, world.mix.copy()
        held = Controls(x=1, fire=True)
        while world.phase_timer > FIXED_DT + 1e-9:
            world.step(FIXED_DT, held)
            self.assertEqual(world.phase, "clear")
            self.assertEqual(world.wave, 1)
            self.assertEqual(world.player.pos, position)
            self.assertEqual(world.time, time)
        world.advance(FIXED_DT * 2, held)
        self.assertEqual(world.phase, "active")
        self.assertEqual(world.wave, 2)
        self.assertEqual(world.transition, 0)
        self.assertEqual(world.mix, mix)
        self.assertEqual(world.shuffle_count, 0)
        self.assertEqual(world.player.health, 65)
        world.advance(FIXED_DT, held)
        self.assertGreater(world.time, time)
        self.assertNotEqual(world.player.pos, position)
        self.assertTrue(world.projectiles or world.effects)

    def test_six_solo_paks_hold_their_identity_and_clear_a_wave(self):
        from system_panic.app import autopilot
        for pak in PAKS:
            with self.subTest(pak=pak.id):
                world = World(Preferences(difficulty="relaxed"), seed=24, solo=pak.id)
                for _ in range(60 * 60):
                    world.advance(1 / 60, autopilot(world))
                    if world.wave > 1 or world.phase == "dead":
                        break
                self.assertGreater(world.wave, 1, f"{pak.id} stalled: kills={world.kills}, hp={world.player.health}")
                self.assertEqual(set(world.mix.values()), {pak.id})
                self.assertEqual(world.shuffle_count, 0)

    def test_all_component_mixes_update_and_fire_safely(self):
        for combo in itertools.product(PAKS, repeat=4):
            world = World(Preferences(shuffle_channels=[]), seed=3)
            world.mix.update({channel: pak.id for channel, pak in zip(GAMEPLAY_CHANNELS, combo)})
            world.cover = world.component("obstacles").build(world)
            world.player.pos = world.safe_position(world.player.pos, 13)
            world.enemies.clear()
            world.spawn_enemy(world.safe_position(Vec(700, 220), away_from=world.player.pos, clearance=160))
            world.phase = "active"
            for _ in range(20):
                world.step(FIXED_DT, Controls(.7, -.7, fire=True, special=True))
            self.assertTrue(math.isfinite(world.player.pos.x) and math.isfinite(world.player.pos.y))
            self.assertGreater(world.player.health, 0)
            self.assertGreater(world.time, 0)
            self.assertTrue(all(math.isfinite(e.health) and math.isfinite(e.pos.x) and math.isfinite(e.pos.y) for e in world.enemies))
            # A valid weapon may need a closed path or a nearby target. Short-lived
            # visuals may also have expired; every mix need not deal immediate damage.

    def test_shuffle_preserves_shared_state_resets_behavior_and_repairs_cover(self):
        world = World(Preferences(enabled=["signal_runner", "void_drifter"]), seed=9)
        world.player.health = 43
        world.score = 800
        world.wave = 3
        original_ids = [e.id for e in world.enemies]
        original_health = [e.health for e in world.enemies]
        world.projectiles.append(CountingShot(Vec(10, 10), Vec(2, 2)))
        for _ in range(15):
            world.shuffle()
            self.assertEqual(world.player.health, 43)
            self.assertEqual((world.score, world.wave), (800, 3))
            self.assertEqual([e.id for e in world.enemies], original_ids)
            self.assertEqual([e.health for e in world.enemies], original_health)
            self.assertTrue(all(type(e).__module__ == type(world.component("enemy")).__module__ for e in world.enemies))
            self.assertEqual(world.projectiles, [])
            self.assertGreaterEqual(world.player.invulnerable, 1.5)
            self.assertFalse(any(c.blocks_body(world.player) and c.overlaps_circle(world.player.pos, 12) for c in world.geometry))

    def test_enabled_filter_coherent_mode_and_locked_channels(self):
        prefs = Preferences(enabled=["sky_forge", "phase_garden"], mix_mode="coherent")
        world = World(prefs, 42)
        for _ in range(10):
            previous = world.mix["pilot"]
            world.shuffle()
            self.assertEqual(len(set(world.mix.values())), 1)
            self.assertNotEqual(world.mix["pilot"], previous)
            self.assertIn(world.mix["pilot"], prefs.enabled)
        prefs.mix_mode = "remix"
        prefs.shuffle_channels = ["weapon"]
        world = World(prefs, 2)
        original = world.mix.copy()
        world.shuffle()
        for channel in ("pilot", "enemy", "music", "background", "obstacles"):
            self.assertEqual(world.mix[channel], original[channel])
        self.assertNotEqual(world.mix["weapon"], original["weapon"])

    def test_fixed_step_is_independent_of_render_rate(self):
        worlds = [World(Preferences(), 142) for _ in range(2)]
        control = Controls(.5, -.3, fire=True)
        for _ in range(600):
            worlds[0].advance(1 / 60, control)
        for _ in range(300):
            worlds[1].advance(1 / 30, control)
        self.assertEqual(worlds[0].mix, worlds[1].mix)
        self.assertAlmostEqual(worlds[0].time, worlds[1].time)
        self.assertEqual(worlds[0].player.pos, worlds[1].player.pos)
        self.assertEqual(worlds[0].score, worlds[1].score)

    def test_projectile_moves_once_and_enemy_death_is_scored_once(self):
        world = World(Preferences(), 0, solo="signal_runner")
        world.phase = "active"
        world.cover = []
        world.projectiles = [CountingShot(Vec(100, 100), Vec(120, 0))]
        world.step(FIXED_DT, Controls())
        self.assertEqual(world.projectiles[0].pos, Vec(101, 100))
        world.enemies[0].health = 0
        world.remove_dead()
        score = world.score
        world.remove_dead()
        self.assertEqual(world.score, score)

    def test_invulnerability_damage_and_death_state(self):
        world = World(Preferences(), 1)
        world.player.invulnerable = 0
        world.hit_player(20)
        self.assertEqual(world.player.health, 80)
        world.hit_player(20)
        self.assertEqual(world.player.health, 80)
        world.player.health = 0
        world.phase = "active"
        world.step(FIXED_DT, Controls())
        self.assertEqual(world.phase, "dead")

    def test_levels_add_one_enemy_and_continue_past_the_former_finale(self):
        for pak in PAKS:
            with self.subTest(pak=pak.id):
                world = World(Preferences(), 24, solo=pak.id)
                for level in range(1, 21):
                    self.assertEqual(world.wave, level)
                    self.assertEqual(len(world.enemies), level)
                    self.assertTrue(all(enemy.health > 0 for enemy in world.enemies))
                    world.enemies.clear()
                    world.phase = "active"
                    world.step(FIXED_DT, Controls())
                    self.assertEqual(world.phase, "clear")
                    for _ in range(round(LEVEL_CLEAR_SECONDS / FIXED_DT) + 1):
                        world.step(FIXED_DT, Controls())
                    self.assertEqual(world.phase, "active")
                    self.assertEqual(world.wave, level + 1)
                    self.assertEqual(world.transition, 0)

    def test_enemy_growth_has_no_late_level_cap(self):
        world = World(Preferences(), 24, solo="signal_runner")
        for previous_level in (98, 99, 100):
            world.wave = previous_level
            world.enemies.clear()
            world.phase = "clear"
            world.phase_timer = 0
            world.step(FIXED_DT, Controls())
            self.assertEqual(world.phase, "active")
            self.assertEqual(world.wave, previous_level + 1)
            self.assertEqual(len(world.enemies), previous_level + 1)

    def test_dense_arena_recovery_is_bounded(self):
        from system_panic.model import Cover
        import pygame
        world = World(Preferences(), 1)
        world.cover = [Cover(pygame.Rect(0, 0, WIDTH, HEIGHT), 36, 36)]
        pos = world.safe_position(Vec(200, 200))
        self.assertFalse(any(circle_rect(pos, 14, c.rect) for c in world.cover))
