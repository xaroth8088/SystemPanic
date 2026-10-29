"""Physical interactions in Storm Loom and Kiln Derby, through the public API."""
import importlib
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
sys.path.insert(0, str(ROOT / 'src'))
import pygame
from system_panic.model import Controls, Cover, Vec, Pilot, circle_rect, FIXED_DT
from system_panic.paks import discover
from system_panic.preferences import Preferences
from system_panic.world import World
from system_panic.graphics import Graphics


class StormKilnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = discover([ROOT / 'paks'])
        pygame.init()
        pygame.display.set_mode((1, 1))

    def world(self, pak, seed=24):
        world = World(Preferences(enabled=list(self.catalog.by_id)), seed, solo=pak, catalog=self.catalog)
        self.addCleanup(world.close)
        world.phase = 'active'
        world.player.pos = Vec(180, 220)
        world.player.vel = Vec()
        world.player.invulnerable = 0
        world.cover = []
        world.enemies.clear()
        return world

    def enemy(self, world, position):
        enemy = world.spawn_enemy(Vec(position))
        enemy.health = enemy.max_health = 1000
        enemy.vel = Vec()
        return enemy

    def attack(self, world, seconds, fire=True):
        for _ in range(round(seconds / FIXED_DT)):
            world.component('weapon').update(world, FIXED_DT, Controls(fire=fire))
            world.update_projectiles(FIXED_DT)

    def test_storm_thread_has_to_travel_then_reels_and_snaps_real_span(self):
        world = self.world('storm_loom')
        target = self.enemy(world, (445, 220))
        weapon = world.component('weapon')
        self.attack(world, .1)
        self.assertEqual(target.health, 1000, 'Distant enemies are not hit by an instant ray')
        self.attack(world, .45)
        self.assertIs(weapon.hook.target, target)
        self.assertLess(target.pos.x, 445)
        self.assertLess(target.health, 987)
        crossing = self.enemy(world, (300, 220))
        outside = self.enemy(world, (300, 290))
        before = target.health
        self.attack(world, .3)
        self.assertLess(crossing.health, 1000, 'The active taut line catches a crossing enemy')
        self.assertEqual(outside.health, 1000)
        self.attack(world, FIXED_DT, False)
        self.assertLess(target.health, before-15)
        self.assertFalse(weapon.hook.alive)

    def test_storm_thread_is_occluded_and_cannot_reel_through_solid_cover(self):
        world = self.world('storm_loom')
        target = self.enemy(world, (450, 220))
        world.cover = [Cover(pygame.Rect(300, 170, 25, 100), 100, 100)]
        self.attack(world, .8)
        self.assertEqual(target.health, 1000)
        world.cover.clear()
        self.attack(world, .7)
        self.assertLess(target.health, 1000)
        health = target.health
        world.cover = [Cover(pygame.Rect(260, 170, 25, 100), 100, 100)]
        world.update_projectiles(FIXED_DT)
        self.assertEqual(target.health, health)
        self.assertFalse(world.component('weapon').hook.alive)

    def test_storm_own_harpoon_rotates_vane_and_release_checks_new_occlusion(self):
        world = self.world('storm_loom')
        target = self.enemy(world,(450,220))
        obstacles = world.component('obstacles')
        vane = obstacles.build(world)[0]
        vane.rect.center = (318,220)
        vane.heading = 0
        world.cover = [vane]
        self.attack(world,.3)
        self.assertAlmostEqual(vane.heading,math.pi/2,'Ordinary weapon contact must dispatch obstacle damage')
        world.cover.clear()
        self.attack(world,.6)
        weapon = world.component('weapon')
        self.assertIs(weapon.hook.target,target)
        world.cover = [Cover(pygame.Rect(260,170,20,100),1000,1000)]
        health = target.health
        # Release dispatch precedes the next projectile update in World.step.
        weapon.update(world,FIXED_DT,Controls(fire=False))
        self.assertEqual(target.health,health,'A just-occluded snap cannot hit through cover')
        self.assertFalse(weapon.hook.alive)

    def test_storm_gate_changes_real_lanes_and_jet_carries_both_teams_far(self):
        world = self.world('storm_loom')
        obstacles = world.component('obstacles')
        vane = obstacles.build(world)[0]
        vane.rect.center = (300,240)
        vane.heading = 0
        world.cover = [vane]
        center = Vec(vane.rect.center)
        world.player.pos = center+Vec(70,-50)
        world.move_body(world.player,Vec(0,100),world.player.radius)
        self.assertGreater(world.player.pos.y,center.y+45,'This lane is open before the physical gate turns')
        health = vane.health
        old_key = vane.navigation_key()
        world.hit_cover(vane, 20)
        self.assertAlmostEqual(vane.heading, math.pi/2)
        self.assertEqual(vane.health, health)
        self.assertNotEqual(vane.navigation_key(),old_key)
        world.player.pos = center+Vec(70,-50)
        world.move_body(world.player,Vec(0,100),world.player.radius)
        self.assertLess(world.player.pos.y,center.y-15,'Rotated solid wings actually close the old lane')
        world.hit_cover(vane, 20)
        self.assertAlmostEqual(vane.heading, math.pi/2, msg='A continuous beam cannot spin the vane every simulation tick')
        vane.heading = 0
        world.player.pos = center+Vec(70,-12)
        enemy = self.enemy(world,center+Vec(110,12))
        outside = self.enemy(world,center+Vec(110,100))
        before = (world.player.pos.copy(),enemy.pos.copy(),outside.pos.copy())
        for _ in range(60): obstacles.update(world,FIXED_DT)
        self.assertGreaterEqual(world.player.pos.x-before[0].x,260)
        self.assertGreaterEqual(enemy.pos.x-before[1].x,260)
        self.assertEqual(outside.pos,before[2])

    def test_storm_jet_has_tactical_wall_impact_damage_and_safe_gate_rotation(self):
        world = self.world('storm_loom')
        obstacles = world.component('obstacles')
        vane = obstacles.build(world)[0]
        vane.rect.center = (150,240)
        vane.heading = 0
        wall = Cover(pygame.Rect(500,150,20,180),1000,1000)
        world.cover = [vane,wall]
        world.player.pos = Vec(260,225)
        enemy = self.enemy(world,(270,255))
        for _ in range(60): obstacles.update(world,FIXED_DT)
        self.assertGreater(world.player.pos.x,480)
        self.assertGreater(enemy.pos.x,480)
        self.assertLessEqual(world.player.health,90)
        self.assertEqual(enemy.health,974,'A half-second jet ride produces one real wall-impact hit')
        self.assertFalse(wall.overlaps_circle(world.player.pos,world.player.radius))
        world.player.pos = Vec(220,240)
        enemy.pos = Vec(80,240)
        vane.turn_cooldown = 0
        world.hit_cover(vane,20)
        self.assertFalse(vane.overlaps_circle(world.player.pos,world.player.radius+1))
        self.assertFalse(vane.overlaps_circle(enemy.pos,enemy.radius+1))

    def test_storm_jet_moves_real_held_thread_endpoints_without_private_pilot_rules(self):
        world = self.world('storm_loom')
        target = self.enemy(world,(445,220))
        self.attack(world,.55)
        weapon = world.component('weapon')
        self.assertIs(weapon.hook.target,target)
        obstacles = world.component('obstacles')
        vane = obstacles.build(world)[0]
        vane.rect.center = (100,220)
        vane.heading = 0
        world.cover = [vane]
        before = world.player.pos.copy(),target.pos.copy()
        for _ in range(48):
            weapon.update(world,FIXED_DT,Controls(fire=True))
            world.update_projectiles(FIXED_DT)
            obstacles.update(world,FIXED_DT)
        self.assertGreater(world.player.pos.x-before[0].x,200)
        self.assertGreater(target.pos.x-before[1].x,150)
        self.assertIs(weapon.hook.target,target)
        self.assertTrue(weapon.hook.alive)

    def test_storm_anchor_reduces_drift_without_damage_immunity(self):
        world = self.world('storm_loom')
        pilot = world.component('pilot')
        world.player.vel = Vec(200, 0)
        pilot.update(world, .1, Controls())
        drifting = world.player.vel.length()
        world.player.vel = Vec(200, 0)
        pilot.update(world, .1, Controls(special=True))
        self.assertLess(world.player.vel.length(), drifting)
        self.assertGreater(world.hit_player(10), 0)

    def test_kiln_pressure_overheats_and_release_cools_without_firing(self):
        world = self.world('kiln_derby')
        weapon = world.component('weapon')
        self.attack(world, .9)
        pressure = weapon.pressure
        self.assertGreater(pressure, .2)
        self.attack(world, .5, False)
        self.assertLess(weapon.pressure, pressure)
        self.attack(world, 4.2)
        self.assertGreater(weapon.locked, 0)
        count = len(world.projectiles)
        self.attack(world, .1)
        self.assertLessEqual(len(world.projectiles), count)

    def test_kiln_hot_marble_rebounds_and_cold_marble_shatters(self):
        world = self.world('kiln_derby')
        module = importlib.import_module(type(world.component('weapon')).__module__)
        wall = Cover(pygame.Rect(300, 100, 20, 240), 1000, 1000)
        world.cover = [wall]
        shot = module.Marble(Vec(280,220), Vec(1,0), 1, 0, world.component('weapon').art)
        shot.update(world, .04)
        self.assertTrue(shot.alive)
        self.assertLess(shot.vel.x, 0)
        self.assertLess(wall.health, 1000)
        cold = module.Marble(Vec(280,220), Vec(1,0), 0, 0, world.component('weapon').art)
        cold.heat = .01
        cold.update(world,.05)
        self.assertFalse(cold.alive)

    def test_kiln_marble_respects_projectile_filter_separately_from_bodies(self):
        world = self.world('kiln_derby')
        module = importlib.import_module(type(world.component('weapon')).__module__)
        class Rail(Cover):
            def blocks_projectile(self, projectile):
                return False
        world.cover = [Rail(pygame.Rect(300, 100, 20, 240), 1000, 1000)]
        shot = module.Marble(Vec(280,220), Vec(1,0), 1, 0, world.component('weapon').art)
        shot.update(world,.15)
        self.assertTrue(shot.alive)
        self.assertGreater(shot.pos.x, 330)
        self.assertGreater(shot.vel.x, 0)

    def test_kiln_ejects_real_hot_slag_that_launches_and_damages_both_teams(self):
        world = self.world('kiln_derby')
        obstacles = world.component('obstacles')
        mouth = obstacles.build(world)[0]
        mouth.rect.center = (200,240)
        mouth.heading = mouth.wait = 0
        world.cover = [mouth]
        enemy = self.enemy(world,(365,250))
        world.player.pos = Vec(365,230)
        before = (world.player.pos.copy(),enemy.pos.copy())
        for _ in range(60): obstacles.update(world,FIXED_DT)
        self.assertGreaterEqual(world.player.pos.x-before[0].x,90)
        self.assertGreaterEqual(enemy.pos.x-before[1].x,90)
        self.assertLessEqual(enemy.health,972)
        self.assertLessEqual(world.player.health,88)
        chunks = [wall for wall in world.cover if hasattr(wall,'hot')]
        self.assertGreaterEqual(len(chunks),2)
        self.assertGreater(max(chunk.pos.x for chunk in chunks),390)

    def test_kiln_successive_volleys_send_real_slag_along_different_lanes(self):
        world = self.world('kiln_derby')
        obstacles = world.component('obstacles')
        mouth = obstacles.build(world)[0]
        mouth.rect.center = (480,240)
        mouth.heading = mouth.wait = 0
        mouth.turn_sign = 1
        world.cover = [mouth]
        world.player.pos = Vec(180,80)
        launches = {}
        for step in range(720):
            obstacles.update(world,FIXED_DT)
            for chunk in world.cover:
                if not hasattr(chunk,'hot'): continue
                if id(chunk) not in launches:
                    self.assertTrue(chunk.hot)
                    self.assertEqual(mouth.turn_duration,0,'A rotating furnace must settle before emission')
                    direction = Vec(math.cos(mouth.heading),math.sin(mouth.heading))
                    self.assertGreater(chunk.vel.normalize().dot(direction),.999999)
                    launches[id(chunk)] = dict(chunk=chunk,volley=mouth.volleys,step=step,
                                               start=chunk.pos.copy(),velocity=chunk.vel.copy())
                record = launches[id(chunk)]
                if step-record['step']==12:
                    record['travel'] = chunk.pos-record['start']
        first = [record for record in launches.values() if record['volley']==1]
        second = [record for record in launches.values() if record['volley']==2]
        self.assertEqual(len(first),3)
        self.assertEqual(len(second),3)
        for record in first:
            self.assertGreater(record['travel'].x,29)
            self.assertAlmostEqual(record['travel'].y,0,places=6)
        for record in second:
            self.assertGreater(record['travel'].y,29)
            self.assertAlmostEqual(record['travel'].x,0,places=6)
        self.assertLess(first[0]['velocity'].normalize().dot(second[0]['velocity'].normalize()),.01)

    def test_kiln_turn_progression_is_seeded_and_never_uses_combat_rng(self):
        def trace(seed):
            world = self.world('kiln_derby',seed)
            obstacles = world.component('obstacles')
            world.cover = obstacles.build(world)
            world.player.pos = Vec(80,80)
            mouths = list(world.cover)
            initial = [(tuple(m.rect),m.heading,m.wait,m.turn_sign) for m in mouths]
            rng_before = world.rng.getstate()
            for _ in range(720): obstacles.update(world,FIXED_DT)
            self.assertEqual(world.rng.getstate(),rng_before)
            self.assertTrue(all(m.volleys>=2 for m in mouths))
            final = [(m.heading,m.turn_target,m.turn_elapsed,m.volleys) for m in mouths]
            chunks = [(wall.pos.copy(),wall.vel.copy(),wall.hot) for wall in world.cover if hasattr(wall,'hot')]
            return initial,final,chunks
        self.assertEqual(trace(24),trace(24))
        self.assertNotEqual(trace(24)[0],trace(73)[0])

    def test_kiln_turn_renders_rotated_source_art_on_a_stationary_safe_base(self):
        world = self.world('kiln_derby')
        obstacles = world.component('obstacles')
        mouth = obstacles.build(world)[0]
        mouth.rect.center = (480,240)
        mouth.heading = mouth.wait = 0
        mouth.turn_sign = 1
        world.cover = [mouth]
        world.player.pos = Vec(442,240)
        enemy = self.enemy(world,(480,202))
        key = mouth.navigation_key()
        positions = world.player.pos.copy(),enemy.pos.copy()
        for _ in range(240):
            obstacles.update(world,FIXED_DT)
            if mouth.turn_duration>0: break
        self.assertGreater(mouth.turn_duration,0)
        headings = []
        for _ in range(round(mouth.turn_duration/FIXED_DT*.5)):
            obstacles.update(world,FIXED_DT)
            headings.append(mouth.heading)
            self.assertEqual(mouth.navigation_key(),key)
            for body in (world.player,enemy):
                self.assertFalse(mouth.overlaps_circle(body.pos,body.radius))
        self.assertTrue(all(after>before for before,after in zip(headings,headings[1:])))
        self.assertGreater(mouth.heading,math.radians(35))
        self.assertLess(mouth.heading,math.radians(55))
        self.assertLess(max(after-before for before,after in zip(headings,headings[1:])),math.radians(1))
        self.assertEqual((world.player.pos,enemy.pos),positions,'Turning machinery does not sweep its collider into nearby actors')
        graphics = Graphics(self.catalog)
        surface = pygame.Surface((960,480),pygame.SRCALPHA)
        surface.fill((0,0,0,0))
        obstacles.draw(graphics,surface,world,mouth)
        source = graphics.render_sprite(obstacles.sprite(world,mouth),58,(255,175,105))
        expected = pygame.transform.rotate(source,-math.degrees(mouth.heading))
        rect = expected.get_rect(center=mouth.rect.center)
        nozzle = Vec(mouth.rect.center)+Vec(math.cos(mouth.heading),math.sin(mouth.heading))*18
        matching = sampled = 0
        for y in range(expected.get_height()):
            for x in range(expected.get_width()):
                pixel = expected.get_at((x,y))
                point = Vec(rect.left+x,rect.top+y)
                if pixel.a<250 or point.distance_to(nozzle)<8: continue
                sampled += 1
                actual = surface.get_at((int(point.x),int(point.y)))
                matching += max(abs(actual[channel]-pixel[channel]) for channel in range(3))<=2
        self.assertGreater(sampled,400)
        self.assertGreater(matching/sampled,.97,'The actual terrain render must rotate the source machinery, not merely its indicator')

    def test_kiln_shooting_hot_slag_creates_solid_shield_and_breaking_clears_it(self):
        world = self.world('kiln_derby')
        obstacles = world.component('obstacles')
        module = importlib.import_module(type(obstacles).__module__)
        slag = module.Slag(Vec(330,220),Vec(300,0))
        world.cover = [slag]
        target = self.enemy(world,(280,220))
        world.move_body(target,Vec(100,0),target.radius)
        self.assertGreater(target.pos.x,370,'Hot slag has no invisible solid collision cage')
        target.pos = Vec(460,220)
        self.attack(world,.4)
        self.assertFalse(slag.hot,'Ordinary weapon contact cools the moving hazard')
        self.assertTrue(slag.blocks_body(target))
        self.assertEqual(slag.vel,Vec())
        target.pos = Vec(280,220)
        world.move_body(target,Vec(100,0),target.radius)
        self.assertLess(target.pos.x,301,'The cooled ceramic is now real body-blocking cover')
        enemy_module = importlib.import_module(type(world.component('enemy')).__module__)
        ash_module = importlib.import_module(enemy_module.__package__+'.ash')
        shot = ash_module.Ash(Vec(420,220),Vec(-1,0),20)
        shot.update(world,.8)
        self.assertFalse(shot.alive,'Cooled cover blocks a real enemy projectile')
        world.hit_cover(slag,slag.health)
        world.update_projectiles(FIXED_DT)
        self.assertNotIn(slag,world.cover)
        target.pos = Vec(280,220)
        world.move_body(target,Vec(100,0),target.radius)
        self.assertGreater(target.pos.x,370)

    def test_kiln_muzzle_cooling_and_moving_cover_never_embed_actors(self):
        world = self.world('kiln_derby')
        obstacles = world.component('obstacles')
        mouth = obstacles.build(world)[0]
        mouth.rect.center = (200,240)
        mouth.heading = mouth.wait = 0
        world.cover = [mouth]
        world.player.pos = Vec(250,240)
        enemy = self.enemy(world,(250,245))
        obstacles.update(world,FIXED_DT)
        chunks = [wall for wall in world.cover if hasattr(wall,'hot')]
        self.assertEqual(len(chunks),1)
        self.assertGreater(world.player.pos.x,330)
        self.assertGreater(enemy.pos.x,330)
        slag = chunks[0]
        world.player.pos = slag.pos.copy()
        enemy.pos = slag.pos+Vec(2,0)
        world.hit_cover(slag,1)
        for body in (world.player,enemy):
            self.assertFalse(body.overlaps_circle(slag.pos,slag.radius+1))
            self.assertTrue(0<body.pos.x<960 and 0<body.pos.y<480)

    def test_kiln_contact_and_cooling_respect_public_actor_footprints(self):
        world = self.world('kiln_derby')
        obstacles = world.component('obstacles')
        module = importlib.import_module(type(obstacles).__module__)
        class WidePilot(Pilot):
            def overlaps_circle(self, position, radius):
                return circle_rect(position,radius,pygame.Rect(self.pos.x-50,self.pos.y-30,100,60))
        world.player = WidePilot(pos=Vec(330,220),radius=5,health=100,max_health=100)
        slag = module.Slag(Vec(330,220),Vec(300,0))
        world.cover = [slag]
        world.hit_cover(slag,1)
        self.assertFalse(world.player.overlaps_circle(slag.pos,slag.radius+1))
        self.assertLess(world.player.pos.x,264,'Cooling clears the public wide footprint, not only radius5')
        world.player.pos = Vec(180,80)
        enemy = self.enemy(world,(340,245))
        enemy.pos = Vec(340,245)
        enemy.radius = 2
        enemy.overlaps_circle = lambda position,radius: circle_rect(position,radius,pygame.Rect(enemy.pos.x-50,enemy.pos.y-30,100,60))
        rolling = module.Slag(Vec(250,220),Vec(300,0))
        world.cover = [rolling]
        obstacles.advance_slag(world,rolling,.1)
        self.assertGreaterEqual(enemy.pos.x,435)
        self.assertEqual(enemy.health,972)

    def test_kiln_slag_bounds_are_conservative_and_inside_arena_when_cooling_at_edges(self):
        world = self.world('kiln_derby')
        obstacles = world.component('obstacles')
        module = importlib.import_module(type(obstacles).__module__)
        world.player.pos = Vec(480,240)
        for position,velocity in ((Vec(944,464),Vec(300,0)),(Vec(16,16),Vec(-300,0)),
                                  (Vec(940.5,460.2),Vec(300,0))):
            slag = module.Slag(position,velocity)
            world.cover = [slag]
            obstacles.advance_slag(world,slag,.1)
            self.assertFalse(slag.hot)
            self.assertGreaterEqual(slag.rect.left,0)
            self.assertGreaterEqual(slag.rect.top,0)
            self.assertLessEqual(slag.rect.right,960)
            self.assertLessEqual(slag.rect.bottom,480)
            self.assertLessEqual(slag.rect.left,slag.pos.x-slag.radius)
            self.assertGreaterEqual(slag.rect.right,slag.pos.x+slag.radius)
            self.assertLessEqual(slag.rect.top,slag.pos.y-slag.radius)
            self.assertGreaterEqual(slag.rect.bottom,slag.pos.y+slag.radius)

    def test_kiln_cooled_cover_expires_and_opens_its_route_after_active_lifetime(self):
        world = self.world('kiln_derby')
        obstacles = world.component('obstacles')
        module = importlib.import_module(type(obstacles).__module__)
        slag = module.Slag(Vec(330,220),Vec(300,0))
        world.cover = [slag]
        world.hit_cover(slag,1)
        self.assertTrue(world.segment_blocked(Vec(180,220),Vec(450,220)))
        for _ in range(899): obstacles.update(world,FIXED_DT)
        self.assertIn(slag,world.cover)
        for _ in range(2): obstacles.update(world,FIXED_DT)
        self.assertNotIn(slag,world.cover)
        self.assertFalse(world.segment_blocked(Vec(180,220),Vec(450,220)))

    def test_kiln_production_is_bounded_furnaces_break_and_level_or_provider_cleans_chunks(self):
        world = self.world('kiln_derby')
        obstacles = world.component('obstacles')
        mouth = obstacles.build(world)[0]
        mouth.rect.center = (200,240)
        mouth.heading = mouth.wait = 0
        world.cover = [mouth]
        world.player.pos = Vec(800,80)
        for _ in range(120): obstacles.update(world,FIXED_DT)
        old_chunks = [wall for wall in world.cover if hasattr(wall,'hot')]
        self.assertTrue(old_chunks)
        world.hit_cover(mouth,mouth.health)
        for _ in range(120): obstacles.update(world,FIXED_DT)
        self.assertTrue(all(wall in old_chunks for wall in world.cover))
        world.solo = None
        world.enabled = ['kiln_derby','signal_runner']
        world.prefs.shuffle_channels = ['music']
        before = list(world.cover)
        world.shuffle()
        self.assertIs(world.component('obstacles'),obstacles)
        self.assertEqual(world.cover,before,'Presentation swaps preserve actual cooled terrain')
        world.prefs.shuffle_channels = ['obstacles']
        world.shuffle()
        self.assertIsNot(world.component('obstacles'),obstacles)
        self.assertTrue(all(all(wall is not chunk for chunk in old_chunks) for wall in world.cover))
        fresh = self.world('kiln_derby')
        foundry = fresh.component('obstacles')
        fresh.cover = foundry.build(fresh)
        fresh.player.pos = Vec(800,80)
        for _ in range(3600):
            foundry.update(fresh,FIXED_DT)
            self.assertLessEqual(sum(hasattr(wall,'hot') for wall in fresh.cover),foundry.MAX_SLAG)
        prior = list(fresh.cover)
        fresh.enemies.clear()
        fresh.start_wave()
        self.assertTrue(all(not hasattr(wall,'hot') for wall in fresh.cover))
        self.assertTrue(all(all(wall is not old for old in prior) for wall in fresh.cover))

    def test_new_layouts_are_seeded_fresh_and_regenerate_without_combat_rng(self):
        for pak in ('storm_loom','kiln_derby'):
            world = self.world(pak)
            obstacles = world.component('obstacles')
            before = world.rng.getstate()
            first = obstacles.build(world)
            second = obstacles.build(world)
            self.assertEqual([tuple(w.rect) for w in first],[tuple(w.rect) for w in second])
            self.assertIsNot(first[0],second[0])
            world.wave += 1
            third = obstacles.build(world)
            self.assertNotEqual([tuple(w.rect) for w in first],[tuple(w.rect) for w in third])
            self.assertEqual(world.rng.getstate(),before)

    def test_new_weapons_forget_cleared_scheduled_objects_and_pickups_survive_swaps(self):
        for pak,other in (('storm_loom','kiln_derby'),('kiln_derby','storm_loom')):
            world = self.world(pak)
            self.enemy(world,(450,220))
            weapon = world.component('weapon')
            self.attack(world,.1)
            old = tuple(world.projectiles)
            self.assertTrue(old)
            world.projectiles.clear()
            self.attack(world,.5)
            self.assertTrue(world.projectiles)
            self.assertTrue(all(s not in old for s in world.projectiles))
            pickup = weapon.create_powerup(world,world.player.pos)
            art = pickup.art
            world.powerups.append(pickup)
            world.mix['weapon'] = other
            world.component('weapon')
            pickup.update(world,FIXED_DT)
            self.assertEqual(world.powerups_collected,1)
            self.assertIs(pickup.art,art)
            self.assertFalse(pickup.alive)

    def test_new_presentation_does_not_change_simulation_or_rng(self):
        graphics = Graphics(self.catalog)
        surface = pygame.Surface((960,480))
        for pak in ('storm_loom','kiln_derby'):
            world = self.world(pak)
            world.cover = world.component('obstacles').build(world)
            self.enemy(world,(450,220))
            self.attack(world,.6)
            for _ in range(150): world.component('obstacles').update(world,FIXED_DT)
            def terrain_state():
                return [(type(wall).__name__,tuple(wall.rect),wall.health,
                         getattr(wall,'hot',None),getattr(wall,'age',None),
                         getattr(wall,'cold_age',None),getattr(wall,'flash',None),
                         getattr(wall,'heading',None),getattr(wall,'turn_elapsed',None),
                         getattr(wall,'turn_duration',None),getattr(wall,'turn_target',None),
                         getattr(wall,'wait',None),getattr(wall,'volleys',None),
                         getattr(wall,'pos',Vec()).copy(),getattr(wall,'vel',Vec()).copy())
                        for wall in world.cover]
            terrain_before = terrain_state()
            before = (world.time,world.rng.getstate(),world.player.pos.copy(),world.player.health,
                      [(e.id,e.pos.copy(),e.health) for e in world.enemies],
                      [(s.pos.copy(),s.alive) for s in world.projectiles])
            world.component('background').draw(surface,world)
            world.component('obstacles').draw_floor(graphics,surface,world)
            for wall in world.cover: wall.draw(graphics,surface,world)
            world.component('pilot').draw(graphics,surface,world)
            for enemy in world.enemies: world.component('enemy').draw(graphics,surface,world,enemy)
            for shot in world.projectiles: shot.draw(graphics,surface,world)
            self.assertEqual(before,(world.time,world.rng.getstate(),world.player.pos,world.player.health,
                                    [(e.id,e.pos,e.health) for e in world.enemies],
                                    [(s.pos,s.alive) for s in world.projectiles]))
            self.assertEqual(terrain_before,terrain_state())

    def test_bellows_only_show_flame_art_during_active_blast_and_kite_stays_upright(self):
        world = self.world('kiln_derby')
        obstacles = world.component('obstacles')
        mouth = obstacles.build(world)[0]
        for flash, frames in ((0.,(0,)),(.1,(2,3)),(0.,(0,))):
            mouth.flash = flash
            expected = [obstacles.art.frame(frame,columns=4).rect for frame in frames]
            self.assertIn(obstacles.sprite(world,mouth).rect,expected)
        storm = self.world('storm_loom')
        pilot = storm.component('pilot')
        for angle in (0,math.pi/2,math.pi,math.pi*1.5):
            storm.player.angle = angle
            self.assertEqual(pilot.sprite_angle(storm,storm.player),0)

    def test_each_complete_pak_installs_alone_with_all_local_assets(self):
        output = ROOT/'output/test-temp'
        output.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output) as temporary:
            for pak in ('storm_loom','kiln_derby'):
                folder = Path(temporary)/pak
                shutil.copytree(ROOT/'paks'/pak,folder/pak,ignore=shutil.ignore_patterns('__pycache__'))
                catalog = discover([folder])
                self.assertEqual(catalog.issues,())
                self.assertEqual(catalog.complete_ids(),(pak,))
                world = World(Preferences(enabled=[pak]),24,solo=pak,catalog=catalog)
                try:
                    world.phase='active'
                    for frame in range(240):
                        world.step(FIXED_DT,Controls(1,0,frame<180,frame<20))
                    self.assertGreater(world.time,0)
                    self.assertTrue(all(math.isfinite(v) for v in world.player.pos))
                finally:
                    world.close()


if __name__ == '__main__':
    unittest.main()
