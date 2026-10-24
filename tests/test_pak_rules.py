"""Behavioral proof that new rules can live in drop-in Paks without host traits."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from system_panic.model import Controls, Enemy, Pilot, Vec, WIDTH, HEIGHT, FIXED_DT
from system_panic.pak_api import EnemyBase, PilotBase, WeaponBase, ProjectileBase
from system_panic.paks import discover
from system_panic.preferences import Preferences
from system_panic.world import World

TEMP = ROOT / "output/test-temp"
TEMP.mkdir(parents=True, exist_ok=True)


class RuleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEMP)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def game(self, role, source):
        pak = self.root / "custom"
        shutil.copytree(ROOT / "paks/signal_runner", pak)
        data = json.loads((pak / "pak.json").read_text())
        data.update(id="custom", name="Custom rules")
        (pak / "pak.json").write_text(json.dumps(data))
        (pak / role / (role + ".py")).write_text(source, encoding="utf-8")
        catalog = discover([self.root])
        self.assertEqual(catalog.issues, ())
        return World(Preferences(enabled=["custom"]), 24, solo="custom", catalog=catalog)

    def test_weapon_receives_every_step_and_owns_arbitrary_trigger_rules(self):
        world = self.game("weapon", '''
from system_panic.pak_api import WeaponBase
class HeldScore(WeaponBase):
    def init(self): self.calls = 0
    def sprite(self, world, entity=None): return None
    def update(self, world, dt, control):
        self.calls += 1
        if control.fire: world.score += 7
''')
        world.phase = "active"
        for _ in range(12):
            world.step(FIXED_DT, Controls(fire=True))
        self.assertEqual(world.component("weapon").calls, 12)
        self.assertEqual(world.score, 84)
        self.assertFalse(world.projectiles)
        self.assertFalse(hasattr(WeaponBase, "cooldown"))
        self.assertFalse(hasattr(world.player, "fire_timer"))

    def test_pilot_owns_body_stats_held_special_and_damage_policy(self):
        world = self.game("pilot", '''
from system_panic.pak_api import PilotBase
from system_panic.model import Pilot, Vec
class TinyPilot(PilotBase):
    def sprite(self, world, entity=None): return None
    def create(self, world, position):
        return Pilot(pos=Vec(position), health=17, max_health=17, radius=3.5)
    def update(self, world, dt, control):
        if control.special: world.player.pos.x += 1
''')
        self.assertEqual(world.player.health, 17)
        self.assertEqual(world.player.radius, 3.5)
        world.phase, world.player.invulnerable = "active", 0
        before = world.player.pos.x
        for _ in range(10):
            world.step(FIXED_DT, Controls(special=True))
        self.assertEqual(world.player.pos.x, before + 10)
        world.hit_player(2)
        world.hit_player(2)
        self.assertEqual(world.player.health, 13)  # No host-imposed hit-recovery rule.
        self.assertFalse(hasattr(world.player, "special_timer"))

    def test_enemy_owns_stats_armor_rewards_and_arbitrary_child_spawns(self):
        world = self.game("enemy", '''
from system_panic.pak_api import EnemyBase
from system_panic.model import Enemy, Vec
class BuddingEnemy(EnemyBase):
    def sprite(self, world, entity=None): return None
    def create(self, world, identity, position):
        enemy = Enemy(id=identity, pos=Vec(position), health=7, max_health=7, radius=8)
        enemy.bud = False
        enemy.clock = 100.
        return enemy
    def bud(self, world, identity, position):
        enemy = self.create(world, identity, position)
        enemy.bud, enemy.health, enemy.max_health, enemy.radius = True, 2, 2, 2
        return enemy
    def advance_enemy(self, world, enemy, dt): enemy.clock += dt * 3
    def take_damage(self, world, enemy, damage): return world.apply_damage(enemy, damage * .25)
    def on_death(self, world, enemy):
        if enemy.bud:
            world.score += 3
        else:
            world.score += 701
            for offset in (-30, 0, 30):
                world.spawn_enemy(enemy.pos + Vec(offset, 0), factory=self.bud)
''')
        enemy = world.enemies[0]
        world.phase = "active"
        for _ in range(20):
            world.step(FIXED_DT, Controls())
        self.assertAlmostEqual(enemy.clock, 100 + 20 * FIXED_DT * 3)
        world.hit_enemy(enemy, 8)
        self.assertEqual(enemy.health, 5)
        world.hit_enemy(enemy, 100)
        world.remove_dead()
        self.assertEqual(len(world.enemies), 3)
        self.assertEqual(world.score, 701)
        self.assertTrue(all(child.health == 2 and child.radius == 2 for child in world.enemies))
        self.assertEqual(len({child.id for child in world.enemies}), 3)
        for child in world.enemies:
            world.hit_enemy(child, 100)
        world.remove_dead()
        world.remove_dead()
        self.assertEqual((world.score, world.kills), (710, 4))
        self.assertFalse(hasattr(EnemyBase, "family"))
        self.assertFalse(hasattr(EnemyBase, "splits"))

    def test_host_does_not_move_expire_bounce_or_classify_a_custom_projectile(self):
        class Teleport(ProjectileBase):
            def __init__(self):
                super().__init__(Vec(-1000, -1000), Vec(123, 456))
                self.steps = 0

            def update(self, world, dt):
                self.steps += 1
                self.pos += Vec(10, 0)
                self.alive = self.steps < 2

            def draw(self, graphics, surface, world):
                pass

        world = World(Preferences(), 24, solo="signal_runner")
        shot = Teleport()
        world.projectiles.append(shot)
        world.update_projectiles(FIXED_DT)
        self.assertEqual(shot.pos, Vec(-990, -1000))
        self.assertIn(shot, world.projectiles)
        world.update_projectiles(FIXED_DT)
        self.assertEqual((shot.steps, shot.pos), (2, Vec(-980, -1000)))
        self.assertNotIn(shot, world.projectiles)

    def test_collision_reports_geometry_without_velocity_or_jump_policy(self):
        world = World(Preferences(), 24, solo="sky_forge")
        world.cover = []
        body = Pilot(pos=Vec(100, HEIGHT - 10), vel=Vec(0, 12), radius=5)
        body.my_jump_count = 4
        motion = world.move_body(body, Vec(0, 50), body.radius)
        self.assertTrue(motion.landed)
        self.assertEqual(body.pos.y, HEIGHT - 5)
        self.assertEqual(body.vel.y, 12)
        self.assertEqual(body.my_jump_count, 4)
        self.assertFalse(hasattr(body, "jumps"))

    def test_void_drifter_implements_its_own_two_fragment_death_rule(self):
        world = World(Preferences(), 24, solo="void_drifter")
        parent = world.enemies[0]
        world.hit_enemy(parent, 1000)
        world.remove_dead()
        self.assertEqual((len(world.enemies), world.score), (2, 100))
        self.assertTrue(all(child.radius == 9 for child in world.enemies))
        self.assertNotIn("fragment", Enemy.__dataclass_fields__)
        for child in world.enemies:
            world.hit_enemy(child, 1000)
        world.remove_dead()
        self.assertEqual((len(world.enemies), world.score), (0, 220))

    def test_launch_weapons_implement_different_cadences_in_their_updates(self):
        class Recorder:
            def __init__(self): self.events = []
            def play_asset(self, asset, **options): self.events.append(asset.path.name)
            def stop_asset(self, asset): pass

        for pak, expected in (("signal_runner", 4), ("iron_circuit", 2)):
            with self.subTest(pak=pak):
                bus = Recorder()
                world = World(Preferences(), 24, solo=pak, audio=bus)
                world.phase, world.cover = "active", []
                world.enemies[0].health = world.enemies[0].max_health = 10000
                world.enemies[0].pos = Vec(900, 400)
                for _ in range(60):
                    world.step(FIXED_DT, Controls(fire=True))
                self.assertEqual(bus.events.count("shot.ogg"), expected)

    def test_ricochet_and_returning_motion_are_pak_projectile_methods(self):
        world = World(Preferences(), 24, solo="iron_circuit")
        world.cover = []
        world.player.pos = Vec(WIDTH - 25, 100)
        world.component("weapon").fire(world, Vec(1, 0))
        shot = world.projectiles[1]
        world.update_projectiles(.1)
        self.assertLess(shot.vel.x, 0)
        self.assertTrue(shot.alive)
        world = World(Preferences(), 24, solo="orbit_keeper")
        world.cover, world.enemies = [], []
        world.player.pos = Vec(200, 200)
        world.component("weapon").fire(world, Vec(1, 0))
        shot = world.projectiles[0]
        for _ in range(72):
            world.update_projectiles(FIXED_DT)
        self.assertGreater(shot.vel.dot(world.player.pos - shot.pos), 0)
        self.assertFalse(hasattr(shot, "return_after"))

    def test_explosion_hits_neighbors_without_a_host_explosion_implementation(self):
        world = World(Preferences(), 24, solo="sky_forge")
        world.cover = []
        world.player.pos = Vec(200, 200)
        first = world.enemies[0]
        second = world.spawn_enemy(Vec(260, 200))
        first.pos = Vec(250, 200)
        for enemy in (first, second):
            enemy.health = enemy.max_health = 100
        world.component("weapon").fire(world, Vec(1, 0))
        for _ in range(12):
            world.update_projectiles(FIXED_DT)
        self.assertLess(first.health, 100)
        self.assertLess(second.health, 100)
        self.assertFalse(hasattr(World, "explode"))
        self.assertFalse(hasattr(World, "spawn_shot"))
