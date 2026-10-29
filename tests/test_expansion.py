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
        shot=next(s for s in world.projectiles if type(s).__name__=='Glaive')
        self.assertLess(shot.vel.x,0)
        for _ in range(360): pilot.update(world,FIXED_DT,Controls(special=True))
        radial=(world.player.pos-Vec(WIDTH/2,HEIGHT/2)).normalize()
        self.assertLess(pilot.aim_direction(world).dot(radial),-.99)
        pilot.update(world,0,Controls())
        pilot.update(world,0,Controls(special=True))
        self.assertGreater(pilot.aim_direction(world).dot(radial),.99)
        before=(world.time,world.player.pos.copy(),world.rng.getstate())
        pilot.aim_direction(world)
        self.assertEqual(before,(world.time,world.player.pos,world.rng.getstate()))

    def test_direction_helpers_respect_explicit_pilot_direction(self):
        world=self.world('orbit_keeper')
        world.player.pos=Vec(650,240)
        pilot=world.component('pilot')
        for pak in get_catalog().paks:
            with self.subTest(weapon=pak.id):
                world.mix['weapon']=pak.id
                # aim() is an author-owned helper, not part of WeaponBase.
                # Contact-only weapons need no aiming helper. Launch behavior
                # for the new directional weapons is checked through update().
                weapon=world.component('weapon')
                aim=getattr(weapon,'aim',None)
                if aim is not None:self.assertGreater(aim(world).x,.99)
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
        self.assertEqual(sum(type(s).__name__=='PlasmaBall' for s in world.projectiles),2)
        world.projectiles.clear()
        weapon.update(world,1,Controls(fire=True))
        self.assertEqual(sum(type(s).__name__=='PlasmaBall' for s in world.projectiles),1)
        self.assertIsNot(world.projectiles[0],ball)

    def test_maze_buffers_turns_and_dash_bounces_both_bodies_on_one_hit(self):
        world=self.world('maze_muncher')
        pilot=world.component('pilot')
        world.player.pos=Vec(100,100)
        pilot.update(world,FIXED_DT,Controls(x=1))
        pilot.update(world,FIXED_DT,Controls(y=1))
        self.assertEqual(world.player.vel.y,0)
        for _ in range(20):pilot.update(world,FIXED_DT,Controls(y=1))
        self.assertGreater(world.player.vel.y,0)
        world.player.pos=Vec(200,200)
        world.player.angle=0
        enemy=world.enemies[0]
        enemy.pos=Vec(240,200)
        enemy.health=enemy.max_health=100
        second=world.spawn_enemy(Vec(300,200))
        second.health=100
        weapon=world.component('weapon')
        for _ in range(30):weapon.update(world,FIXED_DT,Controls(fire=True))
        self.assertEqual(enemy.health,80)
        self.assertEqual(second.health,100)
        self.assertGreater(enemy.pos.x,240)
        self.assertLess(world.player.pos.x,200)
        self.assertLess(world.player.vel.x,0)
        self.assertFalse(world.projectiles)

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
        enemy.pos=world.player.pos+Vec(100,0)
        enemy.health=enemy.max_health=80
        weapon=world.component('weapon')
        for _ in range(26):weapon.update(world,.05,Controls(fire=True))
        self.assertEqual(enemy.health,0)
        self.assertTrue(world.effects)

    def test_vector_only_captures_fully_enclosed_enemies_after_tail_closes(self):
        world=self.world('vector_coil')
        inside=world.enemies[0]
        inside.pos=Vec(260,260)
        outside=world.spawn_enemy(Vec(400,260))
        boundary=world.spawn_enemy(Vec(315,260))
        on_tail=world.spawn_enemy(Vec(260,200))
        original={e.id:e.health for e in world.enemies}
        weapon=world.component('weapon')
        for position in ((200,200),(320,200),(320,320),(200,320)):
            world.player.pos=Vec(position)
            weapon.update(world,FIXED_DT,Controls(fire=True))
        self.assertEqual({e.id:e.health for e in world.enemies},original)
        world.player.pos=Vec(200,190)  # Cross the starting edge, not just a vertex.
        weapon.update(world,FIXED_DT,Controls(fire=True))
        self.assertEqual(inside.health,0)
        for enemy in (outside,boundary,on_tail):
            self.assertEqual(enemy.health,original[enemy.id])
        self.assertFalse(world.projectiles)
        self.assertEqual(len(world.effects),1)
        self.assertTrue(weapon._visual.captured)
        world.remove_dead()
        self.assertEqual(world.kills,1)
        world.remove_dead()
        self.assertEqual(world.kills,1)

    def test_vector_tail_reset_and_straight_retracing_cannot_capture(self):
        world=self.world('vector_coil')
        enemy=world.enemies[0]
        enemy.pos=Vec(260,200)
        health=enemy.health
        weapon=world.component('weapon')
        for position in ((200,200),(320,200),(200,200),(320,200)):
            world.player.pos=Vec(position)
            weapon.update(world,FIXED_DT,Controls(fire=True))
        self.assertEqual(enemy.health,health)
        weapon.update(world,FIXED_DT,Controls())
        self.assertEqual(weapon._points,[])
        weapon.update(world,FIXED_DT,Controls(fire=True))
        weapon.on_shuffle(world,frozenset({'background'}))
        self.assertTrue(weapon._points)
        weapon.on_shuffle(world,frozenset({'pilot'}))
        self.assertEqual(weapon._points,[])
        weapon.update(world,FIXED_DT,Controls(fire=True))
        weapon.on_level_start(world)
        self.assertEqual(weapon._points,[])

    def test_awkward_horizontal_pilot_and_capture_weapon_can_shuffle_out_normally(self):
        world=World(Preferences(enabled=['star_bastion','vector_coil'],shuffle_channels=['weapon']),24)
        world.mix.update(pilot='star_bastion',weapon='vector_coil')
        world.component('pilot')
        world.component('weapon')
        world.cover=[]
        world.phase='active'
        world.shuffle_timer=.1
        held=Controls(x=1,fire=True)
        for _ in range(60):world.step(FIXED_DT,held)
        self.assertEqual(world.mix['pilot'],'star_bastion')
        self.assertEqual(world.mix['weapon'],'star_bastion')
        self.assertEqual(world.shuffle_count,1)
        self.assertEqual(world.phase,'active')
        self.assertTrue(world.projectiles)
        self.assertEqual(world.player.pos.y,HEIGHT-24)

    def test_vector_loop_geometry_handles_concave_shapes_and_both_windings(self):
        world=self.world('vector_coil')
        weapon=world.component('weapon')
        module=sys.modules[type(weapon).__module__]
        polygon=[Vec(p) for p in ((100,100),(300,100),(300,180),(180,180),(180,300),(100,300))]
        body=world.enemies[0]
        body.radius=10
        for shape in (polygon,list(reversed(polygon))):
            body.pos=Vec(140,240)
            self.assertTrue(module.contains_body(shape,body))
            body.pos=Vec(240,240)
            self.assertFalse(module.contains_body(shape,body))
            body.pos=Vec(175,240)
            self.assertFalse(module.contains_body(shape,body))

    def test_vector_pilot_trail_has_no_passive_contact_damage(self):
        world=self.world('vector_coil')
        enemy=world.enemies[0]
        enemy.pos=Vec(245,200)
        health=enemy.health
        for _ in range(60):world.component('pilot').update(world,FIXED_DT,Controls(x=1))
        self.assertEqual(enemy.health,health)
        self.assertFalse(world.projectiles)
        self.assertFalse(world.effects)

    def test_bastion_starts_at_bottom_ignores_vertical_input_and_rolls_horizontally(self):
        world=World(Preferences(),24,solo='star_bastion')
        pilot=world.component('pilot')
        self.assertEqual(world.player.pos.y,HEIGHT-24)
        world.cover=[]
        before=world.player.pos.copy()
        for direction in (-1,1):
            for _ in range(100):pilot.update(world,FIXED_DT,Controls(y=direction))
            self.assertEqual(world.player.pos,before)
            self.assertEqual(world.player.vel.y,0)
        pilot.update(world,.05,Controls(x=1))
        speed=world.player.vel.x
        pilot.update(world,.05,Controls(x=1,y=-1,special=True))
        self.assertGreater(world.player.vel.x,speed)
        self.assertEqual(world.player.pos.y,HEIGHT-24)
        world.cover=[Cover(Rect(int(world.player.pos.x)-20,HEIGHT-44,40,40),36,36)]
        pilot.on_shuffle(world,frozenset({'obstacles'}))
        self.assertEqual(world.player.pos.y,HEIGHT-24)
        from system_panic.model import circle_rect
        self.assertFalse(circle_rect(world.player.pos,world.player.radius,world.cover[0].rect))

    def test_pak_obstacle_policy_protects_impervious_cover_from_shots_and_digging(self):
        for provider,impervious in (('maze_muncher',True),('vector_coil',True),('star_bastion',False)):
            world=self.world('signal_runner')
            world.mix['obstacles']=provider
            world.component('obstacles')
            wall=Cover(Rect(230,188,30,25),36,36)
            world.cover=[wall]
            enemy=world.enemies[0]
            enemy.pos=Vec(500,200)
            weapon=world.component('weapon')
            weapon.update(world,FIXED_DT,Controls(fire=True))
            for _ in range(10):world.update_projectiles(FIXED_DT)
            self.assertEqual(wall.health==36,impervious)
            world.mix['pilot']='burrow_patrol'
            pilot=world.component('pilot')
            world.player.pos=Vec(210,200)
            before=wall.health
            pilot.update(world,.05,Controls(x=1,special=True))
            self.assertEqual(wall.health==before,impervious)

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
