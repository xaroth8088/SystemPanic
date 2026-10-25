"""Distinct classic-inspired mechanics and Orbit Keeper's explicit radial fire intent."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from system_panic.model import Vec,Controls,FIXED_DT,WIDTH,HEIGHT,Cover
from system_panic.paks import discover,get_catalog,CHANNELS
from system_panic.preferences import Preferences
from system_panic.world import World
from pygame import Rect

NEW=('neon_breach','maze_muncher','burrow_patrol','vector_coil','star_bastion','tide_hopper')
TEMP=ROOT/'output/test-temp'
TEMP.mkdir(parents=True,exist_ok=True)


class ExpansionTests(unittest.TestCase):
    def world(self,pak):
        world=World(Preferences(),24,solo=pak)
        world.cover=[]
        world.player.pos=Vec(200,200)
        return world

    def test_orbit_special_toggles_radial_fire_once_per_press_despite_aim_assist(self):
        world=self.world('orbit_keeper')
        world.player.pos=Vec(650,240)
        world.player.angle=0
        pilot=world.component('pilot')
        weapon=world.component('weapon')
        world.enemies[0].pos=Vec(100,240)  # Assisted nearest targeting would point inward.
        self.assertGreater(weapon.aim(world).x,.99)
        self.assertEqual(pilot.status(world),'FIRE OUTWARD')
        pilot.update(world,0,Controls(special=True))
        self.assertLess(weapon.aim(world).x,-.99)
        self.assertEqual(pilot.status(world),'FIRE INWARD')
        weapon.update(world,FIXED_DT,Controls(fire=True))
        self.assertLess(world.projectiles[-1].vel.x,0)
        for _ in range(360): pilot.update(world,FIXED_DT,Controls(special=True))
        radial=(world.player.pos-Vec(WIDTH/2,HEIGHT/2)).normalize()
        self.assertLess(pilot.aim_direction(world).dot(radial),-.99)
        pilot.update(world,0,Controls())
        pilot.update(world,0,Controls(special=True))
        self.assertGreater(pilot.aim_direction(world).dot(radial),.99)
        before=(world.time,world.player.pos.copy(),world.rng.getstate())
        pilot.aim_direction(world)
        self.assertEqual(before,(world.time,world.player.pos,world.rng.getstate()))

    def test_every_shipped_weapon_respects_explicit_pilot_direction(self):
        world=self.world('orbit_keeper')
        world.player.pos=Vec(650,240)
        pilot=world.component('pilot')
        for pak in get_catalog().paks:
            with self.subTest(weapon=pak.id):
                world.mix['weapon']=pak.id
                self.assertGreater(world.component('weapon').aim(world).x,.99)
        pilot.update(world,0,Controls(special=True))
        world.mix['weapon']='sky_forge'
        weapon=world.component('weapon')
        weapon.fire(world,weapon.aim(world))
        self.assertFalse(world.projectiles[-1]._guided)

    def test_each_expansion_is_complete_with_original_independent_assets(self):
        catalog=get_catalog()
        for pak in NEW:
            self.assertTrue(catalog.by_id[pak].complete)
            self.assertEqual(set(catalog.by_id[pak].parts),set(CHANNELS))
            data=json.loads((ROOT/'paks'/pak/'pak.json').read_text())
            self.assertIn('inspired_by',data['authoring'])
        for role,file in (('pilot','pilot_sheet.png'),('enemy','enemy_sheet.png'),('weapon','weapon_sheet.png'),('music','music.ogg'),('obstacles','obstacles_sheet.png')):
            hashes={hashlib.sha256((ROOT/'paks'/pak/role/file).read_bytes()).hexdigest() for pak in NEW}
            self.assertEqual(len(hashes),6,role)

    def test_new_paks_load_alone_and_their_components_form_partial_only_mixes(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as temporary:
            root=Path(temporary)
            for pak in NEW:
                alone=root/pak
                shutil.copytree(ROOT/'paks'/pak,alone/pak,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
                catalog=discover([alone])
                self.assertEqual(catalog.issues,())
                world=World(Preferences(),24,solo=pak,catalog=catalog)
                world.phase='active'
                for _ in range(30): world.step(FIXED_DT,Controls(.7,-.7,True,True))
                world.close()
            partials=root/'partials'
            for role,pak in zip(CHANNELS,NEW):
                folder=partials/pak
                shutil.copytree(ROOT/'paks'/pak/role,folder/role)
                data=json.loads((ROOT/'paks'/pak/'pak.json').read_text())
                data['components']=[role]
                (folder/'pak.json').write_text(json.dumps(data))
            catalog=discover([partials])
            self.assertFalse(catalog.complete_ids())
            self.assertEqual(catalog.issues,())
            world=World(Preferences(),24,catalog=catalog)
            world.phase='active'
            for _ in range(30):world.step(FIXED_DT,Controls(.7,-.7,True,True))
            self.assertEqual(set(world.mix.values()),set(NEW))

    def test_pinball_bounces_and_relaunches_after_transient_cleanup(self):
        world=self.world('neon_breach')
        world.player.pos=Vec(WIDTH-30,100)
        weapon=world.component('weapon')
        world.enemies[0].pos=Vec(400,400)
        weapon.update(world,FIXED_DT,Controls(fire=True))
        ball=world.projectiles[0]
        ball.pos=Vec(WIDTH-10,100)
        ball.guided=False
        ball.vel=Vec(420,0)
        ball.update(world,.05)
        self.assertLess(ball.vel.x,0)
        weapon.update(world,.7,Controls(fire=True))
        self.assertEqual(len(world.projectiles),2)
        world.projectiles.clear()
        weapon.update(world,1,Controls(fire=True))
        self.assertEqual(len(world.projectiles),1)
        self.assertIsNot(world.projectiles[0],ball)

    def test_maze_buffers_turns_and_chomp_wave_hits_each_target_once(self):
        world=self.world('maze_muncher')
        pilot=world.component('pilot')
        world.player.pos=Vec(100,100)
        pilot.update(world,FIXED_DT,Controls(x=1))
        pilot.update(world,FIXED_DT,Controls(y=1))
        self.assertEqual(world.player.vel.y,0)
        for _ in range(20):pilot.update(world,FIXED_DT,Controls(y=1))
        self.assertGreater(world.player.vel.y,0)
        enemy=world.enemies[0]
        enemy.pos=world.player.pos+Vec(100,0)
        enemy.health=enemy.max_health=100
        weapon=world.component('weapon')
        weapon.update(world,FIXED_DT,Controls(fire=True))
        wave=world.projectiles[0]
        for _ in range(60):wave.update(world,FIXED_DT)
        self.assertEqual(enemy.health,73)

    def test_maze_can_escape_cover_not_aligned_to_its_turn_grid(self):
        world=self.world('maze_muncher')
        world.player.pos=Vec(210,200)
        world.cover=[Cover(Rect(230,150,30,140),36,36)]
        pilot=world.component('pilot')
        for _ in range(20):pilot.update(world,FIXED_DT,Controls(x=1))
        before=world.player.pos.copy()
        pilot.update(world,FIXED_DT,Controls(y=1))
        self.assertGreater(world.player.pos.y,before.y)

    def test_drilling_damages_rock_and_inflation_finishes_a_target(self):
        world=self.world('burrow_patrol')
        wall=Cover(Rect(228,188,40,30),36,36)
        world.cover=[wall]
        world.player.pos=Vec(210,200)
        world.component('pilot').update(world,.05,Controls(x=1))
        self.assertLess(wall.health,36)
        enemy=world.enemies[0]
        enemy.pos=Vec(500,200)
        enemy.health=enemy.max_health=80
        weapon=world.component('weapon')
        for _ in range(26):weapon.update(world,.05,Controls(fire=True))
        self.assertEqual(enemy.health,0)
        self.assertTrue(world.effects)

    def test_vector_trail_damages_contacts_and_prism_is_a_scheduled_visual(self):
        world=self.world('vector_coil')
        enemy=world.enemies[0]
        enemy.pos=Vec(245,200)
        health=enemy.health
        pilot=world.component('pilot')
        for _ in range(60):pilot.update(world,FIXED_DT,Controls(x=1))
        self.assertLess(enemy.health,health)
        self.assertEqual(len(world.effects),1)
        weapon=world.component('weapon')
        weapon.update(world,FIXED_DT,Controls(fire=True))
        self.assertEqual(len(world.effects),2)
        self.assertFalse(world.projectiles)

    def test_bastion_stays_in_lower_sky_and_roll_changes_speed(self):
        world=self.world('star_bastion')
        world.player.pos=Vec(400,300)
        pilot=world.component('pilot')
        pilot.update(world,.05,Controls(x=1))
        speed=world.player.vel.x
        pilot.update(world,.05,Controls(x=1,special=True))
        self.assertGreater(world.player.vel.x,speed)
        for _ in range(100):pilot.update(world,FIXED_DT,Controls(y=-1))
        self.assertGreaterEqual(world.player.pos.y,HEIGHT//2-20+world.player.radius)

    def test_hops_travel_over_time_and_harpoon_reels_its_target(self):
        world=self.world('tide_hopper')
        pilot=world.component('pilot')
        before=world.player.pos.copy()
        pilot.update(world,FIXED_DT,Controls(x=1))
        self.assertEqual(world.player.pos,before)
        for _ in range(6):pilot.update(world,FIXED_DT,Controls(x=1))
        self.assertGreater(world.player.pos.x,before.x)
        self.assertLessEqual(world.player.pos.x,before.x+48)
        enemy=world.enemies[0]
        enemy.pos=world.player.pos+Vec(70,0)
        enemy.health=enemy.max_health=100
        weapon=world.component('weapon')
        weapon.update(world,FIXED_DT,Controls(fire=True))
        hook=world.projectiles[0]
        for _ in range(12):hook.update(world,FIXED_DT)
        distance=enemy.pos.distance_to(world.player.pos)
        for _ in range(12):hook.update(world,FIXED_DT)
        self.assertLess(enemy.pos.distance_to(world.player.pos),distance)
        self.assertLess(enemy.health,100)
