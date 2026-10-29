"""Physical stomp, inertial stone and interactive terrain contracts."""
import importlib
import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pygame
from system_panic.model import Controls, Vec, Cover, Pilot, Enemy, FIXED_DT, HEIGHT, WIDTH, circle_rect
from system_panic.paks import discover
from system_panic.preferences import Preferences
from system_panic.world import World


class CanopyRimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = discover([ROOT / "paks"])

    def world(self, pak):
        world = World(Preferences(difficulty="standard"), 24, solo=pak, catalog=self.catalog)
        self.addCleanup(world.close)
        world.cover = []
        world.enemies.clear()
        world.phase = "active"
        world.player.pos = Vec(200, 100)
        return world

    def enemy(self, world, position):
        enemy = world.spawn_enemy(Vec(position))
        enemy.health = enemy.max_health = 1000
        return enemy

    def test_physical_descending_stomp_sweeps_feet_and_bounces(self):
        w = self.world("canopy_capers")
        e = self.enemy(w, (200, 200))
        weapon = w.component("weapon")
        w.player.pos.y, w.player.vel.y = 169.5, 300
        weapon.update(w, FIXED_DT, Controls())
        w.player.pos.y += w.player.vel.y * FIXED_DT
        weapon.update(w, FIXED_DT, Controls())
        self.assertEqual(e.health, 946)
        self.assertLess(w.player.vel.y, 0)
        self.assertEqual(w.player.pos.y, 170)
        self.assertEqual(weapon.chain, 1)
        self.assertFalse(w.projectiles)

    def test_ascending_and_side_contacts_do_not_stomp(self):
        for start, end, velocity in (((200, 172), (200, 169.5), -300),
                                    ((240, 169.5), (240, 172), 300)):
            with self.subTest(start=start):
                w = self.world("canopy_capers")
                e = self.enemy(w, (200, 200))
                w.player.pos = Vec(start)
                w.player.vel.y = velocity
                weapon = w.component("weapon")
                weapon.update(w, FIXED_DT, Controls())
                w.player.pos = Vec(end)
                weapon.update(w, FIXED_DT, Controls())
                self.assertEqual(e.health, 1000)

    def test_automatic_stomp_damage_scales_with_relative_downward_momentum(self):
        damage = []
        for falling, enemy_speed in ((300, 0), (600, 0), (300, 100), (300, -100)):
            w = self.world("canopy_capers")
            enemy = self.enemy(w, (200, 200))
            w.player.pos.y, w.player.vel.y = 169.5, falling
            enemy.vel.y = enemy_speed
            weapon = w.component("weapon")
            weapon.update(w, FIXED_DT, Controls())
            w.player.pos.y += falling * FIXED_DT
            enemy.pos.y += enemy_speed * FIXED_DT
            weapon.update(w, FIXED_DT, Controls())
            damage.append(1000 - enemy.health)
        self.assertEqual(damage, [54, 108, 36, 72])
        self.assertEqual(damage[1], damage[0] * 2)
        self.assertEqual(damage[3], damage[2] * 2)

    def test_primary_jump_is_an_edge_and_held_fire_does_not_repeat(self):
        w = self.world("canopy_capers")
        p, pilot = w.player, w.component("pilot")
        p.pos, p.vel = Vec(300, HEIGHT - p.radius), Vec()
        pilot.grounded = True
        pilot.update(w, FIXED_DT, Controls(fire=True))
        self.assertEqual(pilot.jumps, 1)
        self.assertLess(p.vel.y, -400)
        for _ in range(30):
            pilot.update(w, FIXED_DT, Controls(fire=True))
        self.assertEqual(pilot.jumps, 1)
        self.assertGreater(p.vel.y, -300)
        pilot.update(w, FIXED_DT, Controls())
        pilot.update(w, FIXED_DT, Controls(fire=True))
        self.assertEqual(pilot.jumps, 2)
        self.assertLess(p.vel.y, -400)
        for _ in range(300):
            pilot.update(w, FIXED_DT, Controls(fire=True))
        self.assertEqual(p.pos.y, HEIGHT - p.radius)
        self.assertEqual(p.vel.y, 0)
        pilot.update(w, FIXED_DT, Controls())
        pilot.update(w, FIXED_DT, Controls(fire=True))
        self.assertLess(p.vel.y, -400)

    def test_stomp_cannot_repeat_without_new_crossing_and_upgrades_strengthen(self):
        w = self.world("canopy_capers")
        e = self.enemy(w, (200, 200))
        weapon = w.component("weapon")
        w.powerups_collected = 3
        w.player.pos.y, w.player.vel.y = 169.5, 300
        weapon.update(w, FIXED_DT, Controls())
        w.player.pos.y += 300 * FIXED_DT
        weapon.update(w, FIXED_DT, Controls())
        self.assertAlmostEqual(e.health, 920.08)
        for _ in range(100):
            weapon.update(w, FIXED_DT, Controls(fire=True))
        self.assertAlmostEqual(e.health, 920.08)
        weapon.on_shuffle(w, frozenset({"pilot"}))
        self.assertIsNone(weapon.previous)

    def test_canopy_springs_launch_pilot_and_foreign_enemy_from_above(self):
        w = self.world("canopy_capers")
        obstacles = w.component("obstacles")
        walls = obstacles.build(w)
        spring = next(wall for wall in walls if wall.kind == "spring")
        enemy = self.enemy(w, (500, 420))
        for body in (w.player, enemy):
            body.pos = Vec(spring.rect.centerx, spring.rect.top - body.radius)
            body.vel.y = 200
            self.assertTrue(spring.blocks_body(body))
            self.assertTrue(spring.on_contact(w, body, Vec(0, -1)))
            self.assertEqual(body.vel.y, -475)
            self.assertFalse(spring.blocks_body(body))
        w.player.pos.y = spring.rect.bottom + 25
        w.player.vel.y = -100
        self.assertFalse(spring.blocks_body(w.player))
        self.assertFalse(spring.blocks_projectile(None))

    def test_one_way_spring_catches_a_foreign_body_with_scheduled_motion(self):
        w = self.world("canopy_capers")
        spring = next(wall for wall in w.component("obstacles").build(w) if wall.kind == "spring")
        w.cover = [spring]
        body = self.enemy(w, (40, 40))
        body.pos = Vec(spring.rect.centerx, spring.rect.top - body.radius - 2)
        body.vel = Vec(0, 480)
        w.move_body(body, body.vel * FIXED_DT, body.radius)
        self.assertEqual(body.vel.y, -475)

    def test_stomp_rejects_foreign_pilot_teleport_discontinuities(self):
        w = self.world("canopy_capers")
        e = self.enemy(w, (200, 200))
        weapon = w.component("weapon")
        w.player.vel.y = 300
        weapon.update(w, FIXED_DT, Controls(fire=True))
        w.player.pos.y = 330
        weapon.update(w, FIXED_DT, Controls(fire=True))
        self.assertEqual(e.health, 1000)

    def test_one_way_branch_does_not_trap_walking_at_a_lower_corner(self):
        w = self.world("canopy_capers")
        obstacles = w.component("obstacles")
        leaf = next(wall for wall in obstacles.build(w) if wall.kind == "leaf")
        w.cover = [leaf]
        p = w.player
        p.pos = Vec(leaf.rect.left - p.radius + 2, leaf.rect.top - p.radius + 8)
        for _ in range(60):
            w.component("pilot").update(w, FIXED_DT, Controls(1, 0))
        self.assertGreater(p.pos.x, leaf.rect.left + 90)

    def test_stomp_rejects_enemy_teleport_discontinuities(self):
        w = self.world("canopy_capers")
        e = self.enemy(w, (200, 300))
        weapon = w.component("weapon")
        w.player.vel.y = 300
        weapon.update(w, FIXED_DT, Controls(fire=True))
        e.pos = Vec(200, 80)
        w.player.pos.y = 102.5
        weapon.update(w, FIXED_DT, Controls(fire=True))
        self.assertEqual(e.health, 1000)
        self.assertEqual(w.player.pos.y, 102.5)

    def test_custom_shape_broadphase_is_not_a_flat_platform(self):
        w = self.world("canopy_capers")
        class RoundPylon(Cover):
            def overlaps_circle(self, position, radius):
                return Vec(self.rect.center).distance_to(position) < 21 + radius
        wall = RoundPylon(pygame.Rect(379, 179, 42, 42), 100, 100)
        w.cover = [wall]
        p = w.player
        p.pos, p.vel = Vec(365, 160), Vec(0, 300)
        enemy = self.enemy(w, (40, 40))
        enemy.pos, enemy.vel = Vec(366, 162), Vec(0, 300)
        for _ in range(3):
            w.component("pilot").update(w, FIXED_DT, Controls())
            w.component("enemy").advance_enemy(w, enemy, FIXED_DT)
        self.assertGreater(p.pos.y, 165)
        self.assertGreater(enemy.pos.y, 167)
        self.assertFalse(w.component("pilot").grounded)
        self.assertFalse(enemy.grounded)

    def test_canopy_drawn_feet_match_collision_feet_for_every_frame(self):
        from system_panic.graphics import Graphics
        pygame.display.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))
        w = self.world("canopy_capers")
        graphics = Graphics(self.catalog)
        enemy = self.enemy(w, (400, 240))
        w.player.pos, w.player.invulnerable = Vec(400, 240), 0
        seen = {"pilot": set(), "enemy": set()}
        for phase in range(4):
            w.time = phase / 8 + .001
            for role, body in (("pilot", w.player), ("enemy", enemy)):
                for angle in (0., 3.141592653589793):
                    body.angle = angle
                    surface = pygame.Surface((960, 480), pygame.SRCALPHA)
                    before = (body.pos.copy(), body.health, w.rng.getstate())
                    part = w.component(role)
                    seen[role].add(part.sprite(w, body).rect)
                    if role == "pilot": part.draw(graphics, surface, w)
                    else: part.draw(graphics, surface, w, enemy)
                    opaque = surface.get_bounding_rect(min_alpha=110)
                    self.assertLessEqual(abs(opaque.bottom - (body.pos.y + body.radius)), 1)
                    if role == "enemy":
                        self.assertLessEqual(abs(opaque.top - (body.pos.y - body.radius)), 3)
                    self.assertEqual(before, (body.pos, body.health, w.rng.getstate()))
        self.assertEqual({role: len(frames) for role, frames in seen.items()}, {"pilot": 8, "enemy": 8})

    def test_canopy_leaf_collapses_and_safely_regrows(self):
        w = self.world("canopy_capers")
        obstacles = w.component("obstacles")
        leaf = next(wall for wall in obstacles.build(w) if wall.kind == "leaf")
        w.cover = [leaf]
        w.player.pos = Vec(leaf.rect.centerx, leaf.rect.top - w.player.radius)
        for _ in range(100):
            obstacles.update(w, FIXED_DT)
        self.assertGreater(leaf.missing, 0)
        self.assertFalse(leaf.blocks_body(w.player))
        w.player.pos = Vec(leaf.rect.center)
        for _ in range(400):
            obstacles.update(w, FIXED_DT)
        self.assertGreater(leaf.missing, 0)
        w.player.pos = Vec(40, 40)
        for _ in range(20):
            obstacles.update(w, FIXED_DT)
        self.assertEqual(leaf.missing, 0)
        self.assertEqual(leaf.health, 100)

    def test_enemy_initial_bodies_are_distributed_over_real_platforms(self):
        w = self.world("canopy_capers")
        w.wave = 6
        w.player.pos = Vec(35, 35)
        w.cover = w.component("obstacles").build(w)
        enemies = w.component("enemy")
        for _ in range(6):
            w.spawn_enemy(enemies.spawn_position(w))
        elevations = {round(e.pos.y + e.radius + 3) for e in w.enemies}
        self.assertGreaterEqual(len(elevations), 5)
        self.assertGreaterEqual(sum(e.pos.y < 420 for e in w.enemies), 4)
        self.assertTrue(all(not any(wall.blocks_body(e) and wall.overlaps_circle(e.pos, e.radius)
                                   for wall in w.cover) for e in w.enemies))

    def test_beetle_really_climbs_the_authored_decks_with_active_leaf_updates(self):
        for seed in (24, 73, 2026):
            with self.subTest(seed=seed):
                w = World(Preferences(), seed, solo="canopy_capers", catalog=self.catalog)
                self.addCleanup(w.close)
                w.enemies.clear()
                top = min(w.cover, key=lambda wall: wall.rect.top)
                # Keep the stationary interception target just above the leaf;
                # a test-only frozen player standing on it would load/collapse
                # that leaf without ever falling, which no live player can do.
                w.player.pos = Vec(top.rect.centerx, top.rect.top - w.player.radius - 12)
                enemy = w.spawn_enemy(Vec(100, HEIGHT - 14))
                enemy.pos, enemy.vel, enemy.timer = Vec(100, HEIGHT - 14), Vec(), 0
                landed = set()
                for _ in range(960):
                    w.component("enemy").advance_enemy(w, enemy, FIXED_DT)
                    w.component("obstacles").update(w, FIXED_DT)
                    for wall in w.cover:
                        if (abs(enemy.pos.y + enemy.radius - wall.rect.top) < 1e-6
                                and wall.rect.left - enemy.radius < enemy.pos.x < wall.rect.right + enemy.radius):
                            landed.add(wall.rect.top)
                self.assertGreaterEqual(len(landed), 3)
                self.assertIn(top.rect.top, landed)
                self.assertTrue(any(value < 330 for value in landed))

    def test_beetle_climbs_solid_stairs_and_pursues_back_down_by_motion(self):
        w = self.world("canopy_capers")
        w.cover = [Cover(pygame.Rect(x, y, 150, 14), 100, 100)
                   for x, y in ((120, 390), (300, 310), (470, 235))]
        w.player.pos = Vec(550, 235 - w.player.radius)
        enemy = self.enemy(w, (60, HEIGHT - 14))
        enemy.pos, enemy.vel, enemy.timer = Vec(60, HEIGHT - 14), Vec(), 0
        enemies = w.component("enemy")
        touched = set()
        for _ in range(1200):
            enemies.advance_enemy(w, enemy, FIXED_DT)
            for wall in w.cover:
                if abs(enemy.pos.y + enemy.radius - wall.rect.top) < 1e-6:
                    touched.add(wall.rect.top)
            if 235 in touched:
                break
        self.assertEqual(touched, {390, 310, 235})
        w.player.pos = Vec(80, HEIGHT - w.player.radius)
        enemy.next_patrol = 100
        last = enemy.pos.copy()
        escaped = False
        for _ in range(1200):
            enemies.advance_enemy(w, enemy, FIXED_DT)
            self.assertLess(enemy.pos.distance_to(last), 6)
            last = enemy.pos.copy()
            escaped |= enemy.pos.y + enemy.radius > 320
            if enemy.pos.y + enemy.radius >= HEIGHT - .01:
                break
        self.assertTrue(escaped)
        self.assertAlmostEqual(enemy.pos.y + enemy.radius, HEIGHT)
        self.assertLess(enemy.pos.x, 470)

    def test_floor_quarry_still_gets_platform_flanking_instead_of_a_floor_pile(self):
        w = self.world("canopy_capers")
        w.cover = w.component("obstacles").build(w)
        w.player.pos = Vec(900, HEIGHT - w.player.radius)
        enemies = w.component("enemy")
        for index in range(6):
            enemy = self.enemy(w, (80 + index * 30, HEIGHT - 14))
            enemy.pos = Vec(80 + index * 30, HEIGHT - enemy.radius)
            enemy.grounded, enemy.timer, enemy.next_patrol = True, 0., 0.
        peak_elevated = 0
        landed = set()
        for _ in range(1200):
            for enemy in w.enemies:
                enemies.advance_enemy(w, enemy, FIXED_DT)
                for wall in w.cover:
                    if (abs(enemy.pos.y + enemy.radius - wall.rect.top) < 1e-6
                            and wall.rect.left - enemy.radius < enemy.pos.x < wall.rect.right + enemy.radius):
                        landed.add(wall.rect.top)
            w.component("obstacles").update(w, FIXED_DT)
            peak_elevated = max(peak_elevated, sum(enemy.pos.y + enemy.radius < 420 for enemy in w.enemies))
        self.assertGreaterEqual(peak_elevated, 3)
        self.assertGreaterEqual(len(landed), 3)

    def test_rime_brake_reduces_inertia_and_diagonal_is_normalized(self):
        a = self.world("rime_rink")
        b = self.world("rime_rink")
        a.player.pos, b.player.pos = Vec(450, 240), Vec(450, 240)
        a.player.vel, b.player.vel = Vec(260, 0), Vec(260, 0)
        for _ in range(30):
            a.component("pilot").update(a, FIXED_DT, Controls())
            b.component("pilot").update(b, FIXED_DT, Controls(special=True))
        self.assertLess(b.player.vel.length(), a.player.vel.length() * .3)
        a.player.vel, b.player.vel = Vec(), Vec()
        a.component("pilot").update(a, FIXED_DT, Controls(1, 0))
        b.component("pilot").update(b, FIXED_DT, Controls(1, 1))
        self.assertAlmostEqual(a.player.vel.length(), b.player.vel.length())

    def test_heated_grates_slow_both_teams_without_blocking(self):
        w = self.world("rime_rink")
        obstacles = w.component("obstacles")
        grate = next(wall for wall in obstacles.build(w) if wall.kind == "warm")
        w.cover = [grate]
        enemy = self.enemy(w, grate.rect.center)
        for body in (w.player, enemy):
            body.pos = Vec(grate.rect.center)
            body.vel = Vec(100, 0)
        obstacles.update(w, .25)
        self.assertAlmostEqual(w.player.vel.x, enemy.vel.x)
        self.assertLess(w.player.vel.x, 40)
        self.assertFalse(grate.blocks_body(w.player))
        self.assertFalse(grate.blocks_projectile(None))

    def test_moving_press_pushes_and_hurts_both_teams_with_cooldown(self):
        w = self.world("rime_rink")
        obstacles = w.component("obstacles")
        press = next(wall for wall in obstacles.build(w) if wall.kind == "press")
        press.phase = 0
        press.rect.centerx = round(press.home.x)
        w.cover = [press]
        enemy = self.enemy(w, press.rect.center)
        enemy.pos = Vec(press.rect.center)
        w.player.pos = Vec(press.rect.center)
        w.player.invulnerable = 0
        obstacles.update(w, FIXED_DT)
        self.assertLess(w.player.health, 100)
        self.assertLess(enemy.health, 1000)
        self.assertFalse(press.overlaps_circle(w.player.pos, w.player.radius))
        self.assertFalse(press.overlaps_circle(enemy.pos, enemy.radius))
        health = enemy.health
        enemy.pos = Vec(press.rect.center)
        obstacles.update(w, FIXED_DT)
        self.assertEqual(enemy.health, health)

    def test_press_build_and_first_tick_use_the_same_seeded_phase(self):
        w = self.world("rime_rink")
        obstacles = w.component("obstacles")
        press = next(wall for wall in obstacles.build(w) if wall.kind == "press")
        w.cover = [press]
        initial_x = press.rect.centerx
        w.player.pos = Vec(press.rect.right + w.player.radius + 8, press.rect.centery)
        w.player.invulnerable = 0
        self.assertFalse(press.overlaps_circle(w.player.pos, w.player.radius))
        obstacles.update(w, FIXED_DT)
        self.assertLessEqual(abs(press.rect.centerx - initial_x), 1)
        self.assertEqual(w.player.health, 100)

    def stone(self, w, position, velocity):
        weapon = w.component("weapon")
        module = importlib.import_module(type(weapon).__module__)
        return module.Stone(Vec(position), Vec(velocity), 40, weapon.art, (132, 215, 255))

    def test_curling_stone_swept_hit_push_and_contact_cooldown(self):
        w = self.world("rime_rink")
        enemy = self.enemy(w, (260, 100))
        stone = self.stone(w, (200, 100), (440, 0))
        stone.update(w, .15)
        self.assertLess(enemy.health, 1000)
        self.assertGreater(enemy.pos.x, 260)
        self.assertGreater(enemy.vel.x, 0)
        health = enemy.health
        stone.pos = enemy.pos.copy()
        stone.update(w, FIXED_DT)
        self.assertEqual(enemy.health, health)

    def test_curling_stone_uses_projectile_filter_and_gains_bank_strength(self):
        w = self.world("rime_rink")
        class ProjectileWall(Cover):
            def blocks_body(self, body): return False
            def blocks_projectile(self, projectile): return True
        wall = ProjectileWall(pygame.Rect(230, 50, 20, 100), 100, 100)
        w.cover = [wall]
        stone = self.stone(w, (210, 100), (440, 0))
        stone.update(w, .1)
        self.assertLess(stone.vel.x, 0)
        self.assertGreater(stone.banks, 0)
        self.assertFalse(wall.overlaps_circle(stone.pos, stone.radius))

    def spend_rime_stock(self, w):
        weapon = w.component("weapon")
        for _ in range(weapon.capacity):
            weapon.cooldown = 0
            weapon.update(w, FIXED_DT, Controls(fire=True))
        for index, stone in enumerate(weapon.stones):
            stone.pos, stone.vel, stone.resting = Vec(500+index*35, 300), Vec(), True
        return weapon

    def test_rime_stock_does_not_regenerate_and_settled_stones_never_expire(self):
        w = self.world("rime_rink")
        weapon = self.spend_rime_stock(w)
        original = tuple(weapon.stones)
        self.assertEqual(weapon.stock, 0)
        for _ in range(1200):
            weapon.update(w, FIXED_DT, Controls(fire=True))
            w.update_projectiles(FIXED_DT)
        self.assertEqual(weapon.stock, 0)
        self.assertEqual(tuple(weapon.stones), original)
        self.assertEqual(tuple(w.projectiles), original)
        self.assertTrue(all(stone.alive and stone.resting and stone.age > 9 for stone in original))

    def test_rime_only_actual_pilot_contact_returns_one_stone_and_chimes_once(self):
        w = self.world("rime_rink")
        weapon = self.spend_rime_stock(w)
        calls = []
        class Chime:
            def play(self, **kwargs): calls.append(kwargs)
        weapon.chime = Chime()
        stone = weapon.stones[0]
        w.player.pos = stone.pos+Vec(50, 0)
        stone.update(w, 1.)
        self.assertEqual(weapon.stock, 0)
        self.assertFalse(calls)
        w.player.pos = stone.pos+Vec(24, 0)
        stone.update(w, FIXED_DT)
        stone.update(w, FIXED_DT)
        self.assertEqual(weapon.stock, 1)
        self.assertEqual(weapon.recovered, 1)
        self.assertEqual(len(calls), 1)
        self.assertFalse(stone.alive)
        self.assertEqual(weapon.stock+len(weapon.stones), weapon.capacity)
        weapon.cooldown = 0
        weapon.update(w, FIXED_DT, Controls(fire=True))
        self.assertEqual(weapon.stock, 0)
        self.assertEqual(len(weapon.stones), 4)

    def test_new_rime_throw_cannot_be_reclaimed_at_the_muzzle(self):
        w = self.world("rime_rink")
        weapon = w.component("weapon")
        weapon.update(w, FIXED_DT, Controls(fire=True))
        stone = weapon.stones[0]
        stone.update(w, FIXED_DT)
        self.assertTrue(stone.alive)
        self.assertEqual(weapon.stock, 3)
        self.assertEqual(weapon.recovered, 0)

    def test_rime_recovery_and_impact_use_custom_actor_footprints(self):
        w = self.world("rime_rink")
        weapon = w.component("weapon")
        weapon.update(w, FIXED_DT, Controls(fire=True))
        stone = weapon.stones[0]
        class OffsetPilot(Pilot):
            def overlaps_circle(self, position, radius):
                return circle_rect(position, radius, pygame.Rect(self.pos.x+100, self.pos.y-10, 100, 20))
        w.player = OffsetPilot(pos=Vec(200, 200), radius=5, health=100, max_health=100)
        stone.pos, stone.vel, stone.resting = Vec(350, 200), Vec(), True
        stone.update(w, FIXED_DT)
        self.assertEqual(weapon.stock, 4)
        class OffsetEnemy(Enemy):
            def overlaps_circle(self, position, radius):
                return circle_rect(position, radius, pygame.Rect(self.pos.x+100, self.pos.y-20, 50, 40))
        enemy = OffsetEnemy(id=999, pos=Vec(200, 200), radius=5, health=1000, max_health=1000)
        w.enemies = [enemy]
        shot = self.stone(w, (275, 200), (440, 0))
        shot.update(w, .15)
        self.assertLess(enemy.health, 1000)
        self.assertGreater(enemy.vel.x, 0)

    def test_rime_presentation_swap_preserves_physical_loans_but_gameplay_and_level_reset(self):
        w = self.world("rime_rink")
        weapon = self.spend_rime_stock(w)
        original = tuple(weapon.stones)
        before = [(stone.pos.copy(), stone.age, stone.resting) for stone in original]
        w.solo = None
        w.enabled = ["rime_rink", "signal_runner"]
        w.prefs.shuffle_channels = ["music", "background"]
        w.shuffle()
        self.assertIs(w.component("weapon"), weapon)
        self.assertEqual(tuple(w.projectiles), original)
        self.assertEqual(weapon.stock, 0)
        self.assertEqual(before, [(stone.pos, stone.age, stone.resting) for stone in original])
        w.start_wave()
        self.assertEqual(weapon.stock, weapon.capacity)
        self.assertFalse(weapon.stones)
        self.assertTrue(all(not stone.alive for stone in original))
        weapon = self.spend_rime_stock(w)
        old = tuple(weapon.stones)
        w.projectiles.clear()
        weapon.on_shuffle(w, frozenset({"obstacles"}))
        self.assertEqual(weapon.stock, weapon.capacity)
        self.assertTrue(all(not stone.alive for stone in old))
        weapon.update(w, FIXED_DT, Controls(fire=True))
        final = tuple(weapon.stones)
        w.mix["weapon"] = "signal_runner"
        w.component("weapon")
        self.assertTrue(all(not stone.alive for stone in final))
        self.assertFalse(weapon.stones)

    def test_rime_stones_stay_in_bounds_and_clear_real_custom_moving_cover(self):
        w = self.world("rime_rink")
        rock = self.stone(w, (940, 460), (440, 400))
        for _ in range(2400):
            rock.update(w, FIXED_DT)
            self.assertTrue(rock.alive)
            self.assertTrue(rock.radius <= rock.pos.x <= WIDTH-rock.radius)
            self.assertTrue(rock.radius <= rock.pos.y <= HEIGHT-rock.radius)
            self.assertTrue(22 <= rock.pos.x <= WIDTH-22)
            self.assertTrue(22 <= rock.pos.y <= HEIGHT-22)
        self.assertTrue(rock.resting)
        class Circle(Cover):
            def overlaps_circle(self, position, radius):
                return Vec(self.rect.center).distance_to(position) < 21+radius
        wall = Circle(pygame.Rect(379, 179, 42, 42), 100, 100)
        w.cover = [wall]
        rock.pos, rock.vel, rock.resting = Vec(365, 160), Vec(), True
        rock.update(w, FIXED_DT)
        self.assertEqual(rock.pos, Vec(365, 160), "Empty broad-phase corners cannot move a settled stone")
        rock.pos = Vec(wall.rect.center)
        rock.update(w, FIXED_DT)
        self.assertFalse(wall.overlaps_circle(rock.pos, rock.radius))
        self.assertTrue(rock.alive)

    def test_rime_collected_upgrades_expand_finite_capacity_only_twice(self):
        w = self.world("rime_rink")
        weapon = self.spend_rime_stock(w)
        w.powerups_collected = 1
        weapon.on_powerup(w, 1)
        self.assertEqual((weapon.capacity, weapon.stock), (5, 1))
        w.powerups_collected = 2
        weapon.on_powerup(w, 2)
        self.assertEqual((weapon.capacity, weapon.stock), (6, 2))
        w.powerups_collected = 20
        weapon.on_powerup(w, 20)
        self.assertEqual((weapon.capacity, weapon.stock), (6, 2))
        self.assertEqual(weapon.stock+len(weapon.stones), weapon.capacity)

    def test_rime_demo_physically_skates_to_and_collects_a_spent_stone(self):
        from system_panic.app import autopilot
        w = self.world("rime_rink")
        weapon = self.spend_rime_stock(w)
        self.enemy(w, (800, 350))
        w.player.invulnerable = 0
        for _ in range(600):
            previous = w.player.pos.copy()
            w.step(FIXED_DT, autopilot(w))
            self.assertLess(w.player.pos.distance_to(previous), 4, "Retrieval must use the ordinary pilot motion")
            self.assertEqual(weapon.stock+len(weapon.stones), weapon.capacity)
            if weapon.recovered:
                break
        self.assertGreater(weapon.recovered, 0)
        self.assertGreater(weapon.stock, 0)
        self.assertGreater(w.player.pos.x, 450)

    def test_seeded_new_layouts_are_fresh_and_leave_combat_rng_unchanged(self):
        for pak in ("canopy_capers", "rime_rink"):
            w = self.world(pak)
            obstacles = w.component("obstacles")
            state = w.rng.getstate()
            first = obstacles.build(w)
            second = obstacles.build(w)
            self.assertEqual(state, w.rng.getstate())
            self.assertEqual([tuple(x.rect) for x in first], [tuple(x.rect) for x in second])
            self.assertTrue(all(a is not b for a,b in zip(first,second)))
            w.wave += 1
            self.assertNotEqual([tuple(x.rect) for x in first], [tuple(x.rect) for x in obstacles.build(w)])

    def test_powerup_capture_chime_once_and_expiry(self):
        for pak in ("canopy_capers", "rime_rink"):
            w = self.world(pak)
            weapon = w.component("weapon")
            drop = weapon.create_powerup(w, w.player.pos)
            w.powerups = [drop]
            drop.update(w, FIXED_DT)
            drop.update(w, FIXED_DT)
            self.assertEqual(w.powerups_collected, 1)
            self.assertFalse(drop.alive)
            drop = weapon.create_powerup(w, (800, 400))
            w.powerups = [drop]
            drop.update(w, 50)
            self.assertFalse(drop.alive)


if __name__ == "__main__":
    unittest.main()
