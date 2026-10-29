"""Contracts for folding/returning paper, placed induction rails and shared fields."""
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import pygame
from system_panic.model import Controls, Cover, Enemy, Vec, FIXED_DT, circle_rect
from system_panic.paks import discover, CHANNELS
from system_panic.preferences import Preferences
from system_panic.world import World


class PaperFerricTests(unittest.TestCase):
    def world(self, pak):
        world = World(Preferences(difficulty='standard'), 24, solo=pak)
        self.addCleanup(world.close)
        world.phase = 'active'
        world.cover = []
        world.enemies.clear()
        world.player.pos = Vec(200, 200)
        return world

    def enemy(self, world, position):
        enemy = world.spawn_enemy(Vec(position))
        enemy.health = enemy.max_health = 1000
        return enemy

    def attack(self, world, seconds, fire):
        for _ in range(round(seconds/FIXED_DT)):
            world.component('weapon').update(world, FIXED_DT, Controls(fire=fire))
            world.update_projectiles(FIXED_DT)

    def test_paper_charge_needs_release_and_cannot_make_a_tap_attack(self):
        world = self.world('paper_pilgrimage')
        self.attack(world, .1, True)
        self.attack(world, .1, False)
        self.assertEqual(world.projectiles, [])
        self.attack(world, 1., True)
        weapon = world.component('weapon')
        module = importlib.import_module(type(weapon).__module__)
        self.assertFalse(any(isinstance(shot, module.FoldBlade) for shot in world.projectiles))
        self.assertIsNotNone(weapon.fold)
        self.attack(world, FIXED_DT, False)
        self.assertEqual(len(world.projectiles), 1)
        self.assertEqual(world.projectiles[0].state, 'outbound')
        self.assertGreater(world.projectiles[0].damage, 40)

    def charge_canvas(self, world):
        from system_panic.graphics import Graphics
        pygame.display.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))
        surface = pygame.Surface((960, 480), pygame.SRCALPHA)
        world.component('weapon').fold.draw(Graphics(), surface, world)
        return surface

    def test_paper_charge_folds_through_four_visible_stages_without_an_attack(self):
        world = self.world('paper_pilgrimage')
        weapon = world.component('weapon')
        hashes, stages = [], []
        enemy = self.enemy(world, world.player.pos)
        for target in (.05, .35, .7, 1.1):
            weapon.update(world, target-weapon.charge, Controls(fire=True))
            world.update_projectiles(FIXED_DT)
            fold = weapon.fold
            self.assertIsNotNone(fold)
            self.assertIn(fold, world.projectiles)
            self.assertEqual(fold.vel, Vec())
            self.assertFalse(fold.is_threat_to(world, world.player))
            self.assertEqual(enemy.health, 1000)
            self.assertFalse(weapon.blades)
            surface = self.charge_canvas(world)
            self.assertGreater(pygame.mask.from_surface(surface).count(), 150)
            hashes.append(hashlib.sha256(pygame.image.tobytes(surface, 'RGBA')).hexdigest())
            stages.append(fold.stage)
        self.assertEqual(stages, [0, 1, 2, 3])
        self.assertEqual(len(set(hashes)), 4)
        weapon.update(world, 20., Controls(fire=True))
        self.assertEqual(weapon.charge, 1.1)
        self.assertEqual(weapon.fold.fraction, 1.)
        self.assertEqual(weapon.fold.stage, 3)

    def test_paper_fold_disappears_on_release_and_prunes_host_cleared_displays(self):
        world = self.world('paper_pilgrimage')
        weapon = world.component('weapon')
        self.attack(world, .1, True)
        old = weapon.fold
        weapon.update(world, FIXED_DT, Controls())
        self.assertIsNone(weapon.fold)
        self.assertFalse(old.alive)
        world.update_projectiles(FIXED_DT)
        self.assertEqual(world.projectiles, [])
        self.attack(world, .6, True)
        old = weapon.fold
        world.projectiles.clear()
        weapon.update(world, FIXED_DT, Controls(fire=True))
        self.assertIsNot(old, weapon.fold)
        self.assertFalse(old.alive)
        self.assertEqual(sum(isinstance(shot, type(weapon.fold)) for shot in world.projectiles), 1)
        current = weapon.fold
        weapon.update(world, FIXED_DT, Controls())
        self.assertFalse(current.alive)
        self.assertIsNone(weapon.fold)
        self.assertEqual(len(weapon.blades), 1)
        self.attack(world, .3, True)
        current = weapon.fold
        weapon.deactivate(world)
        self.assertFalse(current.alive)
        self.assertIsNone(weapon.fold)

    def test_paper_fold_cleanup_keeps_existing_swap_and_level_reset_policy(self):
        world = self.world('paper_pilgrimage')
        weapon = world.component('weapon')
        self.attack(world, .6, True)
        weapon.cooldown = .31
        cooldown, old = weapon.cooldown, weapon.fold
        world.projectiles.clear()  # Same scheduling boundary as a real swap.
        weapon.on_shuffle(world, frozenset({'music', 'background'}))
        self.assertFalse(old.alive)
        self.assertIsNone(weapon.fold)
        self.assertEqual(weapon.charge, 0)
        self.assertEqual(weapon.cooldown, cooldown)
        self.assertFalse(weapon.previous_fire)
        weapon.update(world, FIXED_DT, Controls(fire=True))
        self.assertIsNotNone(weapon.fold)
        self.assertAlmostEqual(weapon.charge, FIXED_DT)
        self.assertFalse(weapon.blades)
        old = weapon.fold
        world.start_wave()
        self.assertFalse(old.alive)
        self.assertIsNone(weapon.fold)
        self.assertEqual(weapon.charge, 0)
        self.assertEqual(weapon.cooldown, 0)
        self.assertFalse(weapon.previous_fire)
        weapon.update(world, FIXED_DT, Controls(fire=True))
        self.assertIsNotNone(weapon.fold)
        self.assertAlmostEqual(weapon.charge, FIXED_DT)

    def test_paper_fold_follows_foreign_pilot_and_stays_visible_at_edges(self):
        world = self.world('paper_pilgrimage')
        world.mix['pilot'] = 'neon_breach'
        world.component('pilot')
        weapon = world.component('weapon')
        self.attack(world, 1.1, True)
        for position in (Vec(12, 12), Vec(948, 12), Vec(12, 468), Vec(948, 468), Vec(480, 240)):
            world.player.pos = position
            weapon.fold.pos = Vec(400, 350)  # A later obstacle/pilot relocation.
            surface = self.charge_canvas(world)
            bounds = surface.get_bounding_rect(min_alpha=80)
            self.assertGreater(bounds.width*bounds.height, 150)
            self.assertLess(Vec(bounds.center).distance_to(position), 65)
            self.assertTrue(pygame.Rect(0, 0, 960, 480).contains(bounds))

    def test_paper_fold_render_is_pure_and_reduced_motion_is_steady_even_muted(self):
        world = self.world('paper_pilgrimage')
        weapon = world.component('weapon')
        self.attack(world, .62, True)
        world.prefs.effects = 0.
        normal = []
        for moment in (.1, 1.2):
            world.time = moment
            before = (world.time, world.rng.getstate(), world.player.pos.copy(), world.player.vel.copy(), world.player.health,
                      weapon.charge, weapon.cooldown, weapon.previous_fire, weapon.fold.pos.copy(), weapon.fold.alive)
            surface = self.charge_canvas(world)
            self.assertGreater(pygame.mask.from_surface(surface).count(), 150)
            self.assertEqual(before, (world.time, world.rng.getstate(), world.player.pos, world.player.vel, world.player.health,
                                      weapon.charge, weapon.cooldown, weapon.previous_fire, weapon.fold.pos, weapon.fold.alive))
            normal.append(pygame.image.tobytes(surface, 'RGBA'))
        self.assertNotEqual(normal[0], normal[1])
        world.prefs.reduced_motion = True
        world.time = .1
        first = pygame.image.tobytes(self.charge_canvas(world), 'RGBA')
        world.time = 1.2
        second = pygame.image.tobytes(self.charge_canvas(world), 'RGBA')
        self.assertEqual(first, second)

    def test_paper_charge_drawing_does_not_change_the_simulated_attack_trace(self):
        world = self.world('paper_pilgrimage')
        baseline = self.world('paper_pilgrimage')
        baseline.component('weapon').show_charge = lambda world, held: None
        for scene in (world, baseline):
            self.enemy(scene, (600, 200))
        def state(scene):
            weapon = scene.component('weapon')
            return (scene.time, scene.phase, scene.wave, scene.score, scene.kills, scene.rng.getstate(),
                    tuple(scene.player.pos), tuple(scene.player.vel), scene.player.health,
                    [(enemy.id, tuple(enemy.pos), tuple(enemy.vel), enemy.health) for enemy in scene.enemies],
                    weapon.charge, weapon.cooldown, weapon.previous_fire,
                    [(tuple(blade.pos), tuple(blade.vel), blade.age, blade.state, blade.alive, frozenset(blade.hit)) for blade in weapon.blades],
                    scene.events.copy())
        for step in range(600):
            controls = Controls(1 if step < 60 else 0, 0, step%132 < 90, step in (180, 360))
            world.step(FIXED_DT, controls)
            baseline.step(FIXED_DT, controls)
            if world.component('weapon').fold is not None and step%30 == 0:
                self.charge_canvas(world)
            self.assertEqual(state(world), state(baseline), step)

    def test_paper_unfold_and_return_have_separate_bounded_hit_sets(self):
        world = self.world('paper_pilgrimage')
        weapon = world.component('weapon')
        module = importlib.import_module(type(weapon).__module__)
        blade = module.FoldBlade(Vec(300, 200), Vec(1, 0), 1., 0, weapon.art, weapon)
        enemy = self.enemy(world, (305, 200))
        blade.update(world, FIXED_DT)
        initial = enemy.health
        blade.vel = Vec()
        blade.update(world, FIXED_DT)
        self.assertEqual(enemy.health, initial)
        blade.unfold(world)
        blade.update(world, FIXED_DT)
        self.assertLess(enemy.health, initial)
        unfolded = enemy.health
        blade.update(world, FIXED_DT)
        self.assertEqual(enemy.health, unfolded)
        blade.unfold_age = .12
        blade.update(world, FIXED_DT)
        self.assertEqual(blade.state, 'return')
        self.assertLess(enemy.health, unfolded)
        blade.pos = world.player.pos.copy()
        blade.update(world, FIXED_DT)
        self.assertFalse(blade.alive)

    def test_paper_unfold_does_not_damage_through_solid_cover(self):
        world = self.world('paper_pilgrimage')
        weapon = world.component('weapon')
        module = importlib.import_module(type(weapon).__module__)
        blade = module.FoldBlade(Vec(300, 200), Vec(1, 0), 1., 0, weapon.art, weapon)
        enemy = self.enemy(world, (345, 200))
        world.cover = [Cover(pygame.Rect(320, 160, 10, 80), 100, 100)]
        blade.unfold(world)
        blade.update(world, FIXED_DT)
        self.assertEqual(enemy.health, 1000)

    def test_fold_gates_transport_pilot_and_enemy_and_prevent_ping_pong(self):
        world = self.world('paper_pilgrimage')
        obstacles = world.component('obstacles')
        world.cover = obstacles.build(world)
        gates = [wall for wall in world.cover if hasattr(wall, 'pair')]
        world.player.pos = Vec(gates[0].rect.center)
        enemy = self.enemy(world, gates[2].rect.center)
        world.player.vel, enemy.vel = Vec(100, 50), Vec(-60, 80)
        old_speeds = world.player.vel.length(), enemy.vel.length()
        obstacles.update(world, FIXED_DT)
        self.assertLess(world.player.pos.distance_to(Vec(gates[1].rect.center)), 65)
        self.assertLess(enemy.pos.distance_to(Vec(gates[3].rect.center)), 65)
        self.assertAlmostEqual(world.player.vel.length(), old_speeds[0])
        self.assertAlmostEqual(enemy.vel.length(), old_speeds[1])
        world.player.pos = Vec(gates[1].rect.center)
        enemy.pos = Vec(gates[3].rect.center)
        obstacles.update(world, FIXED_DT)
        self.assertEqual(world.player.pos, Vec(gates[1].rect.center))
        self.assertEqual(enemy.pos, Vec(gates[3].rect.center))
        world.enemies.clear()
        obstacles.update(world, FIXED_DT)
        self.assertNotIn(id(enemy), obstacles.cooldowns)

    def test_shots_open_shutters_for_both_bodies_then_safe_close(self):
        world = self.world('paper_pilgrimage')
        obstacles = world.component('obstacles')
        world.cover = obstacles.build(world)
        shutter = next(wall for wall in world.cover if hasattr(wall, 'opened'))
        enemy = self.enemy(world, (500, 400))
        self.assertTrue(shutter.blocks_body(enemy))
        world.hit_cover(shutter, 5)
        self.assertFalse(shutter.blocks_body(enemy))
        self.assertFalse(shutter.blocks_body(world.player))
        self.assertFalse(shutter.blocks_projectile(None))
        self.assertEqual(shutter.health, 100)
        world.player.pos = Vec(shutter.rect.center)
        obstacles.update(world, 1.3)
        self.assertTrue(shutter.blocks_body(world.player))
        self.assertFalse(shutter.overlaps_circle(world.player.pos, world.player.radius))

    def test_paper_fold_is_input_edge_and_keeps_committed_direction(self):
        world = self.world('paper_pilgrimage')
        pilot = world.component('pilot')
        pilot.update(world, FIXED_DT, Controls(0, -1, special=True))
        self.assertLess(world.player.vel.y, -500)
        pilot.update(world, FIXED_DT, Controls(1, 0, special=True))
        self.assertLess(world.player.vel.y, -500)
        self.assertEqual(world.player.vel.x, 0)
        cooldown = pilot.cooldown
        pilot.update(world, FIXED_DT, Controls(1, 0, special=True))
        self.assertLess(pilot.cooldown, cooldown)

    def ferric_pair(self, world, charge=.8):
        world.player.pos = Vec(200, 200)
        self.attack(world, .1, True)
        self.attack(world, .1, False)
        world.player.pos = Vec(400, 200)
        self.attack(world, charge, True)
        return world.component('weapon')

    def test_ferric_rail_requires_two_spaced_placements_and_release(self):
        world = self.world('ferric_ferry')
        weapon = world.component('weapon')
        self.attack(world, 1., True)
        self.assertEqual(len(weapon.terminals), 1)
        self.assertIsNone(weapon.conduit)
        self.assertEqual(world.projectiles, [])
        self.attack(world, FIXED_DT, False)
        world.player.pos += Vec(20, 0)
        self.attack(world, .5, True)
        self.attack(world, FIXED_DT, False)
        self.assertEqual(len(weapon.terminals), 1)
        self.assertEqual(world.projectiles, [])
        world.player.pos = Vec(400, 200)
        self.attack(world, .8, True)
        self.assertEqual(len(weapon.terminals), 2)
        self.assertTrue(weapon.conduit.powered)
        self.assertEqual(world.projectiles, [])
        world.player.pos = Vec(600, 350)  # Holding does not drag a planted rail.
        self.attack(world, .1, True)
        self.assertEqual(weapon.conduit.start, Vec(400, 200))
        self.assertEqual(weapon.conduit.end, Vec(200, 200))
        weapon.update(world, FIXED_DT, Controls())
        self.assertEqual(len(world.projectiles), 1)
        self.assertEqual(weapon.armature.pos, Vec(400, 200))
        self.assertLess(weapon.armature.vel.x, -600)
        self.assertFalse(weapon.conduit.powered)

    def test_ferric_held_current_and_sweeping_armature_have_real_occlusion_and_impulse(self):
        world = self.world('ferric_ferry')
        weapon = self.ferric_pair(world)
        enemy = self.enemy(world, (300, 200))
        outside = self.enemy(world, (300, 260))
        self.attack(world, .5, True)
        self.assertLess(enemy.health, 1000)
        self.assertEqual(outside.health, 1000)
        health = enemy.health
        weapon.update(world, FIXED_DT, Controls())
        shot = weapon.armature
        shot.update(world, .2)
        self.assertLess(enemy.health, health-80)
        self.assertLess(enemy.pos.x, 300)
        self.assertLess(enemy.vel.x, 0)
        after = enemy.health
        shot.update(world, .01)
        self.assertEqual(enemy.health, after)
        shot.update(world, 1.)
        self.assertFalse(shot.alive)
        self.assertEqual(outside.health, 1000)

    def test_ferric_induction_pulls_both_actors_to_the_fixed_conductor(self):
        world = self.world('ferric_ferry')
        weapon = self.ferric_pair(world)
        world.player.pos = Vec(340, 150)
        enemy = self.enemy(world, (300, 250))
        weapon.update(world, .1, Controls(fire=True))
        self.assertGreater(world.player.pos.y, 150)
        self.assertLess(enemy.pos.y, 250)
        self.assertEqual(weapon.conduit.start, Vec(400, 200))
        self.assertEqual(weapon.conduit.end, Vec(200, 200))
        world.cover = [Cover(pygame.Rect(270, 220, 100, 10), 100, 100)]
        enemy.pos = Vec(300, 250)
        weapon.update(world, .1, Controls(fire=True))
        self.assertEqual(enemy.pos, Vec(300, 250))

    def test_ferric_rail_respects_solid_cover_but_conducts_through_body_only_rails(self):
        world = self.world('ferric_ferry')
        weapon = self.ferric_pair(world)
        class Barrier(Cover):
            strikes = 0
            def damage(self, world, amount):
                self.strikes += 1
                return 0.
        barrier = Barrier(pygame.Rect(285, 170, 20, 60), 100, 100)
        world.cover = [barrier]
        enemy = self.enemy(world, (250, 200))
        self.attack(world, .5, True)
        self.assertEqual(enemy.health, 1000)
        weapon.update(world, FIXED_DT, Controls())
        shot = weapon.armature
        shot.update(world, 1.)
        self.assertFalse(shot.alive)
        self.assertGreater(barrier.strikes, 0)
        self.assertEqual(enemy.health, 1000)
        class BodyRail(Barrier):
            def blocks_projectile(self, projectile): return False
        world.cover = [BodyRail(barrier.rect, 100, 100)]
        self.attack(world, .8, True)
        weapon.update(world, FIXED_DT, Controls())
        weapon.armature.update(world, 1.)
        self.assertLess(enemy.health, 1000)

    def test_ferric_rewiring_and_host_clears_never_resurrect_an_armature(self):
        world = self.world('ferric_ferry')
        weapon = self.ferric_pair(world)
        weapon.update(world, FIXED_DT, Controls())
        old = weapon.armature
        world.player.pos = Vec(600, 200)
        weapon.update(world, FIXED_DT, Controls(fire=True))
        self.assertFalse(old.alive)
        self.assertEqual([terminal.position for terminal in weapon.terminals], [Vec(400, 200), Vec(600, 200)])
        self.assertEqual(weapon.conduit.start, Vec(600, 200))
        self.assertEqual(weapon.conduit.end, Vec(400, 200))
        self.attack(world, .8, True)
        weapon.update(world, FIXED_DT, Controls())
        world.projectiles.clear()
        weapon.update(world, FIXED_DT, Controls())
        self.assertIsNone(weapon.armature)
        self.assertEqual(world.projectiles, [])
        shapes = list(world.geometry)
        weapon.on_shuffle(world, frozenset({'music'}))
        self.assertTrue(all(shape in world.geometry for shape in shapes))
        self.assertEqual(weapon.charge, 0)
        world.start_wave()
        self.assertFalse(any(shape in world.geometry for shape in shapes))
        self.assertEqual(weapon.terminals, [])
        self.ferric_pair(world)
        owned = list(weapon.terminals)+[weapon.conduit]
        world.mix['weapon'] = 'signal_runner'
        world.component('weapon')
        self.assertFalse(any(shape in world.geometry for shape in owned))

    def test_ferric_unrelated_swap_preserves_held_edge_charge_and_planted_geometry(self):
        world = self.world('ferric_ferry')
        weapon = self.ferric_pair(world, charge=.6)
        shapes = world.geometry.copy()
        before = [terminal.position.copy() for terminal in weapon.terminals]
        charge = weapon.charge
        world.player.pos = Vec(600, 350)
        weapon.on_shuffle(world, frozenset({'music', 'background'}))
        self.assertAlmostEqual(weapon.charge, charge)
        self.assertTrue(weapon.previous_fire)
        weapon.update(world, FIXED_DT, Controls(fire=True))
        self.assertEqual([terminal.position for terminal in weapon.terminals], before)
        self.assertTrue(all(shape in world.geometry for shape in shapes))

    def test_ferric_charge_threshold_upgrade_formulas_and_finite_lifetime(self):
        world = self.world('ferric_ferry')
        weapon = self.ferric_pair(world, charge=.1)
        weapon.update(world, FIXED_DT, Controls())
        self.assertEqual(world.projectiles, [])
        module = importlib.import_module(type(weapon).__module__)
        basic = module.Armature(Vec(400, 200), Vec(200, 200), 1., 0, weapon.art, (250, 170, 123))
        upgraded = module.Armature(Vec(400, 200), Vec(200, 200), 2.4, 20, weapon.art, (250, 170, 123))
        world.powerups_collected = 20
        self.assertEqual(weapon.maximum_charge(world), 2.4)
        self.assertGreater(upgraded.damage, basic.damage)
        self.assertGreater(upgraded.radius, basic.radius)
        upgraded.update(world, 2.9)
        self.assertFalse(upgraded.alive)

    def test_ferric_armature_respects_full_circle_width_at_a_grazing_obstacle(self):
        world = self.world('ferric_ferry')
        weapon = world.component('weapon')
        module = importlib.import_module(type(weapon).__module__)
        class GrazingWall(Cover):
            strikes = 0
            def damage(self, world, amount):
                self.strikes += 1
                return 0.
        wall = GrazingWall(pygame.Rect(285, 208, 20, 40), 100, 100)
        world.cover = [wall]
        self.assertFalse(wall.overlaps_segment(Vec(400, 200), Vec(200, 200)))
        shot = module.Armature(Vec(400, 200), Vec(200, 200), 1., 0, weapon.art, (250, 170, 123))
        shot.update(world, 1.)
        self.assertFalse(shot.alive)
        self.assertEqual(wall.strikes, 1)
        self.assertGreater(shot.pos.x, 300)

    def test_ferric_current_round_cap_cannot_reach_through_thin_or_grazing_cover(self):
        for wall_rect, first, second, target in ((pygame.Rect(200, 100, 1, 200), Vec(300, 200), Vec(100, 200), Vec(218, 200)),
                                                (pygame.Rect(285, 202, 20, 40), Vec(200, 200), Vec(400, 200), Vec(250, 200))):
            with self.subTest(wall=wall_rect):
                world = self.world('ferric_ferry')
                world.cover = [Cover(wall_rect, 1000, 1000)]
                enemy = self.enemy(world, target)
                world.player.pos = first
                self.attack(world, .1, True)
                self.attack(world, .1, False)
                world.player.pos = second
                self.attack(world, 1., True)
                self.assertEqual(enemy.health, 1000)
                conduit = world.component('weapon').conduit
                self.assertFalse(world.cover[0].overlaps_circle(conduit.live_end, 4))

    def test_ferric_current_and_armature_use_foreign_enemy_contact_footprints(self):
        world = self.world('ferric_ferry')
        class OffsetEnemy(Enemy):
            def overlaps_circle(self, position, radius):
                return circle_rect(position, radius, pygame.Rect(self.pos.x+150, self.pos.y-30, 100, 60))
        enemy = OffsetEnemy(pos=Vec(100, 245), radius=5, health=1000, max_health=1000, id=999)
        world.enemies = [enemy]
        world.player.pos = Vec(180, 220)
        self.attack(world, .1, True)
        self.attack(world, .1, False)
        world.player.pos = Vec(450, 220)
        self.attack(world, .5, True)
        weapon = world.component('weapon')
        self.assertLess(enemy.health, 1000)
        health = enemy.health
        weapon.update(world, FIXED_DT, Controls())
        weapon.armature.update(world, .3)
        self.assertLess(enemy.health, health-50)

    def test_ferric_weapon_alone_can_plant_and_discharge_with_five_foreign_roles(self):
        temporary_root = ROOT/'output/test-temp'
        temporary_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as temporary:
            partial = Path(temporary)/'ferric_weapon_only'
            shutil.copytree(ROOT/'paks/ferric_ferry/weapon', partial/'weapon', ignore=shutil.ignore_patterns('__pycache__'))
            metadata = json.loads((ROOT/'paks/ferric_ferry/pak.json').read_text())
            metadata.update(id='ferric_weapon_only', name='Independent induction rail', components=['weapon'])
            (partial/'pak.json').write_text(json.dumps(metadata))
            catalog = discover([Path(temporary), ROOT/'paks'])
            self.assertEqual(catalog.issues, ())
            mix = dict.fromkeys(CHANNELS, 'signal_runner')
            mix['weapon'] = 'ferric_weapon_only'
            world = World(Preferences(), 24, catalog=catalog, fixed_mix=mix)
            try:
                world.cover = []
                world.enemies.clear()
                enemy = self.enemy(world, (300, 200))
                weapon = self.ferric_pair(world)
                self.assertEqual(len(weapon.terminals), 2)
                health = enemy.health
                weapon.update(world, FIXED_DT, Controls())
                self.assertIsNotNone(weapon.armature)
                weapon.armature.update(world, 1.)
                self.assertLess(enemy.health, health-75)
                self.assertTrue(all(shape in world.geometry for shape in weapon.terminals))
            finally:
                world.close()
            self.assertFalse(world.geometry)

    def test_pylon_fields_affect_both_actors_and_reverse_on_actual_hits(self):
        world = self.world('ferric_ferry')
        obstacles = world.component('obstacles')
        world.cover = obstacles.build(world)
        pylon = next(wall for wall in world.cover if hasattr(wall, 'polarity'))
        world.cover = [pylon]
        world.player.pos = pylon.center+Vec(-65, 0)
        enemy = self.enemy(world, pylon.center+Vec(65, 0))
        before = world.player.pos.x, enemy.pos.x
        obstacles.update(world, .1)
        self.assertGreater(world.player.pos.x, before[0])
        self.assertLess(enemy.pos.x, before[1])
        world.hit_cover(pylon, 10)
        self.assertEqual(pylon.polarity, -1)
        world.hit_cover(pylon, 10)
        self.assertEqual(pylon.polarity, -1)  # No multiple flips within a burst.
        before = world.player.pos.x, enemy.pos.x
        obstacles.update(world, .1)
        self.assertLess(world.player.pos.x, before[0])
        self.assertGreater(enemy.pos.x, before[1])
        self.assertEqual(pylon.health, 100)

    def test_pylon_curves_moving_projectiles_without_integrating_them(self):
        world = self.world('ferric_ferry')
        obstacles = world.component('obstacles')
        world.cover = obstacles.build(world)
        pylon = next(wall for wall in world.cover if hasattr(wall, 'polarity'))
        world.cover = [pylon]
        weapon = world.component('weapon')
        module = importlib.import_module(type(weapon).__module__)
        armature = module.Armature(pylon.center+Vec(60, 0), pylon.center+Vec(60, 200), .8, 0, weapon.art, (250, 170, 123))
        speed = armature.vel.length()
        world.projectiles.append(armature)
        before = armature.pos.copy()
        obstacles.update(world, .1)
        self.assertEqual(armature.pos, before)
        self.assertLess(armature.vel.x, 0)
        self.assertAlmostEqual(armature.vel.length(), speed)

    def test_ferric_circle_geometry_is_not_its_bounds_and_rails_pass_shots(self):
        world = self.world('ferric_ferry')
        obstacles = world.component('obstacles')
        world.cover = obstacles.build(world)
        pylon = next(wall for wall in world.cover if hasattr(wall, 'polarity'))
        corner = Vec(pylon.rect.topleft)
        self.assertFalse(pylon.overlaps_circle(corner, 1))
        self.assertTrue(pylon.overlaps_circle(pylon.center, 1))
        self.assertFalse(pylon.overlaps_segment(corner, corner+Vec(0, 2)))
        self.assertIsNotNone(pylon.navigation_key())
        rail = next(wall for wall in world.cover if not hasattr(wall, 'polarity'))
        self.assertTrue(rail.blocks_body(world.player))
        self.assertFalse(rail.blocks_projectile(None))

    def test_pak_layouts_are_seeded_fresh_and_do_not_consume_combat_rng(self):
        for pak in ('paper_pilgrimage', 'ferric_ferry'):
            world = self.world(pak)
            obstacles = world.component('obstacles')
            before = world.rng.getstate()
            first = obstacles.build(world)
            second = obstacles.build(world)
            self.assertEqual([tuple(wall.rect) for wall in first], [tuple(wall.rect) for wall in second])
            self.assertTrue(all(a is not b for a, b in zip(first, second)))
            self.assertEqual(world.rng.getstate(), before)
            world.wave += 1
            third = obstacles.build(world)
            self.assertNotEqual([tuple(wall.rect) for wall in first], [tuple(wall.rect) for wall in third])

    def test_copied_complete_paks_and_complementary_partial_roles_are_independent(self):
        temporary_root = ROOT/'output/test-temp'
        temporary_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as temporary:
            root = Path(temporary)
            for pak in ('paper_pilgrimage', 'ferric_ferry'):
                target = root/pak
                shutil.copytree(ROOT/'paks'/pak, target/pak, ignore=shutil.ignore_patterns('__pycache__'))
                catalog = discover([target])
                self.assertEqual(catalog.issues, ())
                self.assertEqual(catalog.complete_ids(), (pak,))
                world = World(Preferences(), 24, solo=pak, catalog=catalog)
                world.phase = 'active'
                for step in range(120): world.step(FIXED_DT, Controls(1, 0, step < 90, step == 0))
                world.close()
            partial = root/'partial'
            for index, role in enumerate(CHANNELS):
                source = 'paper_pilgrimage' if index%2 else 'ferric_ferry'
                target = partial/role
                shutil.copytree(ROOT/'paks'/source/role, target/role, ignore=shutil.ignore_patterns('__pycache__'))
                metadata = json.loads((ROOT/'paks'/source/'pak.json').read_text())
                metadata.update(id=f'partial_{role}', components=[role])
                (target/'pak.json').write_text(json.dumps(metadata))
            catalog = discover([partial])
            self.assertEqual(catalog.issues, ())
            self.assertFalse(catalog.complete_ids())
            world = World(Preferences(), 24, catalog=catalog)
            world.phase = 'active'
            for step in range(120): world.step(FIXED_DT, Controls(1, 1, step < 90))
            world.close()

    def test_rendering_is_read_only_and_weapon_drops_capture_handles(self):
        pygame.init()
        pygame.display.set_mode((1, 1))
        from system_panic.graphics import Graphics
        graphics = Graphics()
        surface = pygame.Surface((960, 480))
        try:
            for pak in ('paper_pilgrimage', 'ferric_ferry'):
                world = self.world(pak)
                world.cover = world.component('obstacles').build(world)
                self.enemy(world, (550, 240))
                self.attack(world, .8, True)
                self.attack(world, FIXED_DT, False)
                before = (world.rng.getstate(), world.time, world.player.pos.copy(),
                          [(enemy.pos.copy(), enemy.health) for enemy in world.enemies])
                graphics.draw_world(surface, world)
                graphics.draw_world(surface, world)
                self.assertEqual(before, (world.rng.getstate(), world.time, world.player.pos,
                                          [(enemy.pos, enemy.health) for enemy in world.enemies]))
                weapon = world.component('weapon')
                pickup = weapon.create_powerup(world, world.player.pos)
                self.assertIs(pickup.art, weapon.art)
                self.assertEqual(pickup.chime.path.parent, ROOT/'paks'/pak/'weapon')
                world.powerups.append(pickup)
                pickup.update(world, FIXED_DT)
                pickup.update(world, FIXED_DT)
                self.assertEqual(world.powerups_collected, 1)
        finally:
            pygame.quit()


if __name__ == '__main__':
    unittest.main()
