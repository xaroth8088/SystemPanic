"""Collectible ownership, shape collision, hazards and the requested Pak mechanics."""
import importlib
import math
import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT","1")
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from pygame.rect import Rect
from system_panic.model import Vec,Controls,Cover,Pilot,FIXED_DT,WIDTH,HEIGHT
from system_panic.pak_api import PowerupBase
from system_panic.paks import get_catalog
from system_panic.preferences import Preferences
from system_panic.world import World


class PowerupTests(unittest.TestCase):
    def world(self,pak="signal_runner"):
        world=World(Preferences(difficulty="relaxed"),24,solo=pak)
        world.cover=[]
        world.enemies.clear()
        world.player.pos=Vec(200,200)
        world.phase="active"
        return world

    def test_exact_tenth_kill_spawns_at_dead_enemy_and_is_counted_once(self):
        world=self.world()
        for count in range(1,31):
            enemy=world.spawn_enemy(Vec(300+count,200))
            enemy.health=0
            position=enemy.pos.copy()
            world.remove_dead()
            self.assertEqual(len(world.powerups),count//10)
            if count%10==0:self.assertEqual(world.powerups[-1].pos,position)
            world.remove_dead()
            self.assertEqual(world.kills,count)
        self.assertEqual(len(world.powerups),3)
        pickup=world.powerups[0]
        self.assertTrue(world.collect_powerup(pickup))
        self.assertFalse(world.collect_powerup(pickup))
        self.assertEqual(world.powerups_collected,1)

    def test_drop_survives_level_and_weapon_changes_and_upgrades_active_weapon(self):
        world=self.world()
        pickup=world.component("weapon").create_powerup(world,Vec(450,300))
        world.powerups.append(pickup)
        world.start_wave()
        self.assertIn(pickup,world.powerups)
        world.mix["weapon"]="sky_forge"
        weapon=world.component("weapon")
        notifications=[]
        weapon.on_powerup=lambda w,count:notifications.append(count)
        self.assertTrue(world.collect_powerup(pickup))
        self.assertEqual(notifications,[1])
        world.start_wave()
        self.assertEqual(world.powerups_collected,1)

    def test_each_pak_owns_a_distinct_collectible_with_local_assets_and_pickup(self):
        classes=set()
        for pak in get_catalog().complete_ids():
            with self.subTest(pak=pak):
                world=self.world(pak)
                weapon=world.component("weapon")
                pickup=weapon.create_powerup(world,Vec(400,300))
                self.assertIsInstance(pickup,PowerupBase)
                self.assertEqual(pickup.pos,Vec(400,300))
                classes.add(type(pickup))
                self.assertEqual(Path(pickup.art.path).parent,ROOT/"paks"/pak/"weapon")
                world.powerups=[pickup]
                pickup.update(world,.1)
                self.assertTrue(math.isfinite(pickup.pos.x) and math.isfinite(pickup.pos.y))
                pickup.pos=world.player.pos.copy()
                if hasattr(pickup,"anchor"):pickup.anchor=world.player.pos.copy()
                pickup.update(world,0)
                self.assertEqual(world.powerups_collected,1)
        self.assertEqual(len(classes),12)

    def test_pickup_updates_freeze_during_glitch_and_level_clear(self):
        world=self.world("star_bastion")
        pickup=world.component("weapon").create_powerup(world,Vec(600,100))
        world.powerups=[pickup]
        world.enemies=[world.component("enemy").create(world,1,Vec(500,100))]
        before=pickup.pos.copy()
        world.transition=.25
        world.step(FIXED_DT,Controls())
        self.assertEqual(pickup.pos,before)
        world.transition=0
        world.phase="clear"
        world.phase_timer=1
        world.step(FIXED_DT,Controls())
        self.assertEqual(pickup.pos,before)
        world.phase="active"
        world.step(FIXED_DT,Controls())
        self.assertGreater(pickup.pos.y,before.y)

    def test_each_damage_weapon_improves_at_higher_pickup_count(self):
        for pak in get_catalog().complete_ids():
            if pak=="vector_coil":continue
            damage=[]
            for count in (0,5):
                world=self.world(pak)
                world.powerups_collected=count
                world.player.angle=0
                enemy=world.spawn_enemy(Vec(300,200))
                enemy.pos=world.player.pos+world.component("weapon").aim(world)*100
                enemy.health=enemy.max_health=10000
                for _ in range(48):
                    world.component("weapon").update(world,FIXED_DT,Controls(fire=True))
                    world.update_projectiles(FIXED_DT)
                damage.append(10000-enemy.health)
            self.assertGreater(damage[1],damage[0],(pak,damage))

    def test_vector_live_line_bounces_and_gains_charge_damage_only_with_powerups(self):
        for count in (0,3):
            world=self.world("vector_coil")
            world.powerups_collected=count
            weapon=world.component("weapon")
            for p in ((240,150),(240,250)):
                world.player.pos=Vec(p)
                weapon.update(world,FIXED_DT,Controls(fire=True))
            enemy=world.spawn_enemy(Vec(280,200))
            enemy.pos=Vec(270,200)
            enemy.health=100
            enemy.vel=Vec(-120,0)
            motion=world.move_body(enemy,Vec(-50,0),enemy.radius)
            self.assertFalse(motion.normals)  # Shape response was already consumed.
            self.assertGreater(enemy.pos.x,240)
            self.assertGreater(enemy.vel.x,0)
            self.assertEqual(enemy.health,100-4*count)
            enemy.pos,enemy.vel=Vec(270,200),Vec(-120,0)
            enemy.timer=10
            world.component("enemy").advance_enemy(world,enemy,.3)
            self.assertGreater(enemy.vel.x,0)

    def test_vector_carves_solid_areas_and_releases_them_when_weapon_is_replaced(self):
        world=self.world("vector_coil")
        weapon=world.component("weapon")
        for p in ((200,200),(320,200),(320,320),(200,320),(200,190)):
            world.player.pos=Vec(p)
            weapon.update(world,FIXED_DT,Controls(fire=True))
        self.assertEqual(len(weapon._areas),1)
        area=weapon._areas[0]
        body=Pilot(pos=Vec(350,260),radius=11)
        world.move_body(body,Vec(-80,0),body.radius)
        self.assertFalse(area.overlaps_circle(body.pos,body.radius))
        self.assertGreater(body.pos.x,300)
        weapon.update(world,FIXED_DT,Controls())
        self.assertIn(area,world.geometry)
        weapon.on_shuffle(world,frozenset({"music"}))
        self.assertIn(area,world.geometry)
        world.mix["weapon"]="signal_runner"
        world.component("weapon")
        self.assertNotIn(area,world.geometry)
        self.assertFalse(world._geometry)

    def test_star_bolts_expire_instead_of_wrapping(self):
        world=self.world("star_bastion")
        world.player.pos=Vec(950,200)
        weapon=world.component("weapon")
        weapon.aim=lambda w:Vec(1,0)
        weapon.update(world,FIXED_DT,Controls(fire=True))
        for shot in world.projectiles:
            shot.guided=False
            shot.update(world,.1)
            self.assertFalse(shot.alive)
            self.assertGreater(shot.pos.x,WIDTH)

    def test_edge_to_edge_vector_capture_leaves_a_walkable_boundary(self):
        world=self.world("vector_coil")
        weapon=world.component("weapon")
        points=[Vec(p) for p in ((15,15),(945,15),(945,465),(15,465),(15,10))]
        world.player.pos=points[0].copy()
        weapon.update(world,FIXED_DT,Controls(fire=True))
        for start,end in zip(points,points[1:]):
            steps=math.ceil(start.distance_to(end)/100)
            for i in range(1,steps+1):
                world.player.pos=start.lerp(end,i/steps)
                weapon.update(world,FIXED_DT,Controls(fire=True))
        self.assertEqual(len(weapon._areas),1)
        area=weapon._areas[0]
        self.assertFalse(area.overlaps_circle(world.player.pos,world.player.radius))
        before=world.player.pos.copy()
        world.move_body(world.player,Vec(300,0),world.player.radius)
        self.assertGreater(world.player.pos.x-before.x,290)

    def test_neon_vertical_input_does_not_change_position_or_edge(self):
        positions=[]
        for y in (-1,0,1):
            world=self.world("neon_breach")
            pilot=world.component("pilot")
            for _ in range(30):pilot.update(world,FIXED_DT,Controls(y=y))
            positions.append(world.player.pos.copy())
        self.assertEqual(positions[0],positions[1])
        self.assertEqual(positions[1],positions[2])

    def test_burrow_range_breaks_pressure_and_powerups_extend_it_without_full_screen_reach(self):
        world=self.world("burrow_patrol")
        weapon=world.component("weapon")
        enemy=world.spawn_enemy(Vec(345,200))
        enemy.health=enemy.max_health=100
        weapon.update(world,.2,Controls(fire=True))
        self.assertLess(enemy.health,100)
        enemy.pos=Vec(500,200)
        health=enemy.health
        for _ in range(100):weapon.update(world,FIXED_DT,Controls(fire=True))
        self.assertEqual(enemy.health,health)
        self.assertLessEqual(weapon._line.start.distance_to(weapon._line.end),weapon.reach(world)+1e-6)
        world.powerups_collected=100
        self.assertLessEqual(weapon.reach(world),300)

    def test_phase_chain_is_reduced_and_grows_only_through_upgrades(self):
        for count,expected in ((0,2),(3,3)):
            world=self.world("phase_garden")
            world.powerups_collected=count
            for i in range(6):
                enemy=world.spawn_enemy(Vec(300+i*40,200))
                enemy.health=100
            world.component("weapon").fire(world,Vec(1,0))
            self.assertEqual(sum(e.health<100 for e in world.enemies),expected)

    def test_orbit_rings_move_once_per_vertical_press(self):
        world=self.world("orbit_keeper")
        pilot=world.component("pilot")
        world.player.pos=Vec(640,240)
        pilot.activate(world)
        initial=pilot._orbit_radius
        pilot.update(world,FIXED_DT,Controls(y=-1))
        first=pilot._orbit_radius
        self.assertLess(first,initial)
        for _ in range(120):pilot.update(world,FIXED_DT,Controls(y=-1))
        self.assertEqual(pilot._orbit_radius,first)
        pilot.update(world,FIXED_DT,Controls())
        pilot.update(world,FIXED_DT,Controls(y=-1))
        self.assertLess(pilot._orbit_radius,first)

    def test_glaive_leaves_screen_and_returns_to_pilot_alive(self):
        world=self.world("orbit_keeper")
        world.player.pos=Vec(WIDTH-30,240)
        weapon=world.component("weapon")
        weapon.fire(world,Vec(1,0))
        shot=world.projectiles[0]
        offscreen=False
        for _ in range(100):
            shot.update(world,FIXED_DT)
            offscreen|=shot.pos.x>WIDTH
            if not shot.alive:break
        self.assertTrue(offscreen)
        self.assertLess(shot.vel.x,0)
        for _ in range(360):
            if not shot.alive:break
            shot.update(world,FIXED_DT)
        self.assertFalse(shot.alive)
        self.assertLess(shot.pos.distance_to(world.player.pos),25)

    def test_permanent_signal_phase_sky_geometry_ignores_damage(self):
        for pak in ("signal_runner","phase_garden","sky_forge"):
            world=self.world(pak)
            walls=world.component("obstacles").build(world)
            for wall in walls:
                before=wall.health
                self.assertEqual(world.hit_cover(wall,100000),0)
                self.assertEqual(wall.health,before)

    def test_sky_forge_body_lands_without_sprite_clipping_or_tunneling(self):
        world=self.world("sky_forge")
        world.cover=[Cover(Rect(100,260,240,16),36,36)]
        world.player.pos=Vec(200,170)
        world.player.vel=Vec(0,460)
        pilot=world.component("pilot")
        for _ in range(40):pilot.update(world,.025,Controls())
        self.assertAlmostEqual(world.player.pos.y,260-22,places=3)
        self.assertLessEqual(world.player.pos.y+22,260)
        self.assertEqual(world.player.vel.y,0)
        self.assertTrue(pilot._grounded)

    def test_tracks_are_varied_closed_lanes_with_body_only_rails(self):
        world=self.world("iron_circuit")
        part=world.component("obstacles")
        shapes=set()
        for level in range(1,9):
            world.wave=level
            walls=part.build(world)
            shapes.add(len(part.points))
            self.assertGreater(len(walls),10)
            self.assertTrue(all(not wall.blocks_projectile(None) for wall in walls))
            rail=walls[0]
            middle=(rail.a+rail.b)/2
            normal=Vec(-(rail.b-rail.a).y,(rail.b-rail.a).x).normalize()
            body=Pilot(pos=middle+normal*35,radius=10)
            world.cover=walls
            before=body.pos.copy()
            world.move_body(body,-normal*60,body.radius)
            self.assertGreater((body.pos-middle).dot(normal),0)
            self.assertLess(body.pos.distance_to(before),60)
            self.assertFalse(world.segment_blocked(middle+normal*35,middle-normal*35))
        self.assertGreaterEqual(len(shapes),3)

    def test_black_hole_pulls_bodies_shots_and_pickups_and_comets_cross_then_expire(self):
        world=self.world("void_drifter")
        part=world.component("obstacles")
        world.cover=part.build(world)
        hole=part.holes[0]
        world.player.pos=hole.pos+Vec(120,0)
        world.component("weapon").fire(world,Vec(1,0))
        shot=world.projectiles[0]
        shot.pos=hole.pos+Vec(100,0)
        pickup=world.component("weapon").create_powerup(world,hole.pos+Vec(90,0))
        world.powerups=[pickup]
        before=[obj.pos.distance_to(hole.pos) for obj in (world.player,shot,pickup)]
        part.update(world,.1)
        after=[obj.pos.distance_to(hole.pos) for obj in (world.player,shot,pickup)]
        self.assertTrue(all(b<a for a,b in zip(before,after)))
        world.time=part._next_comet+.1
        part.update(world,.01)
        self.assertEqual(len(part.comets),1)
        comet=part.comets[0]
        position=comet.pos.copy()
        part._next_comet=10000
        for _ in range(50):part.update(world,.1)
        self.assertNotEqual(comet.pos,position)
        for _ in range(100):part.update(world,.1)
        self.assertNotIn(comet,world.cover)
