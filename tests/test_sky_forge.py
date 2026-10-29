"""Sky Forge landings and ordinary walking through the real collision resolver."""
import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pygame.rect import Rect
from system_panic.model import Controls, Cover, FIXED_DT, Vec
from system_panic.preferences import Preferences
from system_panic.world import World


class SkyForgeTests(unittest.TestCase):
    def world(self):
        world = World(Preferences(), 24, solo="sky_forge")
        self.addCleanup(world.close)
        world.cover = [Cover(Rect(100, 260, 240, 16), 36, 36)]
        world.enemies.clear()
        return world

    def test_edge_landings_allow_walking_onto_deck_without_jumping(self):
        for dt in (FIXED_DT, .025):
            for edge, direction in ((100, 1), (340, -1)):
                for overhang in (1, 10, 20, 21.9):
                    with self.subTest(dt=dt, edge=edge, overhang=overhang):
                        world = self.world()
                        pilot = world.component("pilot")
                        world.player.pos = Vec(edge - direction * overhang, 170)
                        world.player.vel = Vec(0, 100)
                        for _ in range(round(1 / dt)):
                            pilot.update(world, dt, Controls())
                        self.assertTrue(pilot._grounded)
                        self.assertEqual(world.player.vel.y, 0)
                        self.assertAlmostEqual(world.player.pos.y, 238, places=3)
                        for _ in range(30):
                            pilot.update(world, dt, Controls())
                            self.assertAlmostEqual(world.player.pos.y, 238, places=3)
                        before = world.player.pos.copy()
                        for _ in range(round(.25 / dt)):
                            pilot.update(world, dt, Controls(x=direction))
                        self.assertAlmostEqual((world.player.pos.x - before.x) * direction, 55)
                        self.assertAlmostEqual(world.player.pos.y, 238, places=3)
                        self.assertFalse(world.cover[0].overlaps_circle(world.player.pos, world.player.radius))

    def test_walk_off_edge_falls_and_landing_restores_double_jump(self):
        world = self.world()
        pilot = world.component("pilot")
        world.player.pos = Vec(350, 170)
        for _ in range(120):
            pilot.update(world, FIXED_DT, Controls())
        for jump in range(2):
            before = world.player.pos.y
            pilot.update(world, FIXED_DT, Controls(y=-1))
            self.assertLess(world.player.pos.y, before)
            self.assertEqual(pilot._jumps, jump + 1)
            pilot.update(world, FIXED_DT, Controls())
        for _ in range(240):
            pilot.update(world, FIXED_DT, Controls())
        self.assertEqual(pilot._jumps, 0)
        self.assertAlmostEqual(world.player.pos.y, 238, places=3)
        for _ in range(60):
            pilot.update(world, FIXED_DT, Controls(x=1))
        self.assertGreater(world.player.pos.y, 260)

    def test_side_and_ceiling_contacts_do_not_snap_onto_deck_or_restore_jumps(self):
        for position, velocity, control in (
                ((60, 268), (0, 0), Controls(x=1)),
                ((200, 310), (0, -330), Controls())):
            with self.subTest(position=position):
                world = self.world()
                pilot = world.component("pilot")
                pilot._jumps = 2
                world.player.pos, world.player.vel = Vec(position), Vec(velocity)
                pilot.update(world, .1, control)
                self.assertGreater(world.player.pos.y, 260)
                self.assertEqual(pilot._jumps, 2)
                self.assertFalse(pilot._grounded)
                self.assertFalse(world.cover[0].overlaps_circle(world.player.pos, world.player.radius))

    def test_custom_shape_bounds_and_destroyed_cover_do_not_create_deck_tops(self):
        class EmptyShape(Cover):
            def overlaps_circle(self, position, radius):
                return False

        for cover in (EmptyShape(Rect(100, 260, 240, 16), 36, 36),
                      Cover(Rect(100, 260, 240, 16), 0, 36)):
            with self.subTest(cover=cover):
                world = self.world()
                world.cover = [cover]
                world.player.pos = Vec(200, 170)
                for _ in range(90):
                    world.component("pilot").update(world, FIXED_DT, Controls())
                self.assertGreater(world.player.pos.y, 300)

    def test_blocked_walk_toward_deck_does_not_create_support_in_midair(self):
        world = self.world()
        world.cover.append(Cover(Rect(99, 100, 10, 150), 36, 36))
        world.player.pos = Vec(77, 238)
        for _ in range(60):
            world.component("pilot").update(world, FIXED_DT, Controls(x=1))
        self.assertGreater(world.player.pos.y, 250)


if __name__ == "__main__":
    unittest.main()
