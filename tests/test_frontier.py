"""Behavioral contracts for the six original, independently installed new Paks."""
import ast
import importlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import pygame
from system_panic.model import Controls, Cover, Vec, FIXED_DT
from system_panic.paks import get_catalog, discover, CHANNELS
from system_panic.preferences import Preferences
from system_panic.world import World

NEW=('pulse_abbey','scrap_ballet','glasswake','bloom_siege','echo_vault','tidal_choir')


class FrontierTests(unittest.TestCase):
    def world(self, pak):
        w=World(Preferences(difficulty='standard'),24,solo=pak)
        self.addCleanup(w.close)
        w.cover=[]
        w.player.pos=Vec(200,200)
        w.enemies.clear()
        w.phase='active'
        return w

    def enemy(self, w, position=(300,200)):
        enemy=w.spawn_enemy(Vec(position))
        enemy.health=enemy.max_health=1000
        return enemy

    def attack(self, w, seconds, fire):
        weapon=w.component('weapon')
        for _ in range(round(seconds/FIXED_DT)):
            weapon.update(w,FIXED_DT,Controls(fire=fire))
            w.update_projectiles(FIXED_DT)

    def test_complete_install_and_six_complementary_partial_roles_have_no_external_dependencies(self):
        directory=ROOT/'output/test-temp'
        directory.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=directory) as temporary:
            root=Path(temporary)
            for pak in NEW:
                target=root/pak
                shutil.copytree(ROOT/'paks'/pak,target/pak,ignore=shutil.ignore_patterns('__pycache__'))
                catalog=discover([target])
                self.assertEqual(catalog.issues,())
                self.assertEqual(catalog.complete_ids(),(pak,))
                w=World(Preferences(),24,solo=pak,catalog=catalog)
                w.phase='active'
                for frame in range(180):w.step(FIXED_DT,Controls(1,0,frame<120,frame==0))
                w.close()
            target=root/'partial'
            for role,pak in zip(CHANNELS,NEW):
                folder=target/pak
                shutil.copytree(ROOT/'paks'/pak/role,folder/role)
                data=json.loads((ROOT/'paks'/pak/'pak.json').read_text())
                data['components']=[role]
                (folder/'pak.json').write_text(json.dumps(data))
            catalog=discover([target])
            self.assertEqual(catalog.issues,())
            self.assertFalse(catalog.complete_ids())
            w=World(Preferences(),24,catalog=catalog)
            w.phase='active'
            for frame in range(180):w.step(FIXED_DT,Controls(1,0,frame<120,frame==0))
            w.close()

    def test_source_imports_are_role_local_or_public_engine_contracts(self):
        for pak in NEW:
            for path in (ROOT/'paks'/pak).rglob('*.py'):
                tree=ast.parse(path.read_text())
                for node in ast.walk(tree):
                    if isinstance(node,ast.ImportFrom):
                        self.assertLessEqual(node.level,1,path)
                        self.assertNotIn(node.module or '',NEW,path)

    def test_legacy_quadrant_exporter_preserves_new_row_animation_assets_and_ledger(self):
        from tools.assetforge import export_expansion
        with tempfile.TemporaryDirectory(dir=ROOT/'output') as temporary:
            root=Path(temporary)
            pak=root/'paks/new_rows'
            (pak/'pilot').mkdir(parents=True)
            (root/'assets').mkdir()
            (pak/'pak.json').write_text(json.dumps({'id':'new_rows','authoring':{'animation_grid':[4,4],'sheet_source':'not-a-quadrant-atlas.png'}}))
            art=pak/'pilot/pilot_sheet.png'
            art.write_bytes(b'original row atlas')
            records=[{'file':'paks/new_rows/pilot/pilot_sheet.png','operation':'row extraction'}]
            ledger=root/'assets/pak-exports.json'
            ledger.write_text(json.dumps(records))
            with patch.object(export_expansion,'ROOT',root):export_expansion.main()
            self.assertEqual(art.read_bytes(),b'original row atlas')
            self.assertEqual(json.loads(ledger.read_text()),records)

    def test_pulse_requires_release_and_rewards_the_visual_beat_without_double_hits(self):
        damage=[]
        for phase in (0.,.3):
            w=self.world('pulse_abbey')
            enemy=self.enemy(w)
            self.attack(w,.6,True)
            self.assertEqual(enemy.health,1000)
            w.time=phase
            self.attack(w,FIXED_DT,False)
            self.attack(w,.8,False)
            damage.append(1000-enemy.health)
            after=enemy.health
            self.attack(w,1.,False)
            self.assertEqual(enemy.health,after)
        self.assertGreater(damage[0],damage[1]*1.5)

    def test_salvage_orbits_then_launches_with_inherited_momentum_and_rebuilds_after_clear(self):
        w=self.world('scrap_ballet')
        self.enemy(w,(700,200))
        weapon=w.component('weapon')
        self.attack(w,.9,True)
        orbiters=weapon.orbiters()
        self.assertGreaterEqual(len(orbiters),1)
        self.assertTrue(all(not s.launched for s in orbiters))
        self.assertTrue(all(25<s.pos.distance_to(w.player.pos)<80 for s in orbiters))
        w.player.vel=Vec(0,150)
        self.attack(w,FIXED_DT,False)
        self.assertTrue(all(s.launched and s.vel.length()>400 for s in orbiters))
        self.assertTrue(any(s.vel.y>30 for s in orbiters))
        w.projectiles.clear()
        self.attack(w,.1,True)
        self.assertTrue(weapon.active)
        self.assertFalse(any(s in orbiters for s in weapon.active))

    def test_perfect_resonance_parries_hostile_objects_but_offbeat_does_not(self):
        for perfect in (False,True):
            w=self.world('pulse_abbey')
            weapon=w.component('weapon')
            shots=importlib.import_module(type(weapon).__module__)
            hazards=importlib.import_module(type(w.component('enemy')).__module__)
            hostile=hazards.Bolt(Vec(250,200),Vec(),10)
            ring=shots.Resonance(w.player.pos,.6,perfect,0)
            w.projectiles=[hostile,ring]
            ring.update(w,.12)
            self.assertEqual(hostile.alive,not perfect)

    def test_only_launched_scrap_damages_and_returns_to_recoverable_debris(self):
        w=self.world('scrap_ballet')
        weapon=w.component('weapon')
        module=importlib.import_module(type(weapon).__module__)
        shot=module.Salvage(weapon,Vec(234,200))
        enemy=self.enemy(w,(234,200))
        shot.update(w,.1)
        self.assertEqual(enemy.health,1000)
        shot.state='orbit'
        shot.update(w,.1)
        self.assertEqual(enemy.health,1000)
        shot.launch(w,Vec(1,0))
        shot.update(w,.01)
        self.assertLess(enemy.health,970)
        self.assertEqual(shot.state,'free')
        after=enemy.health
        shot.update(w,.01)
        self.assertEqual(enemy.health,after)

    def test_weevils_avoid_mature_threats_while_stalking_but_commit_to_their_locked_charge(self):
        w=self.world('bloom_siege')
        weapon=w.component('weapon')
        module=importlib.import_module(type(weapon).__module__)
        e=self.enemy(w,(340,200))
        pod=module.Pod(Vec(290,200),weapon,0)
        pod.growth=1.
        part=w.component('enemy')
        e.timer=2
        part.advance_enemy(w,e,0)
        before=e.vel.x
        w.projectiles.append(pod)
        part.advance_enemy(w,e,0)
        self.assertGreater(e.vel.x,before)
        e.state,e.timer,e.target='windup',.01,Vec(200,200)
        part.advance_enemy(w,e,.02)
        self.assertEqual(e.state,'charge')
        self.assertLess(e.vel.x,0)

    def test_glass_ray_banks_and_overheat_requires_a_real_cooling_window(self):
        w=self.world('glasswake')
        w.prefs.aim_assist=False
        w.player.angle=0
        enemy=self.enemy(w,(650,200))
        weapon=w.component('weapon')
        self.attack(w,.1,True)
        ray=next(s for s in w.projectiles if type(s).__name__=='Ray')
        self.assertGreaterEqual(len(ray.segments),3)
        self.assertEqual(round(ray.segments[0][1].x),958)
        self.assertGreater(1000-enemy.health,0)
        self.attack(w,3.2,True)
        self.assertTrue(weapon.locked)
        self.assertFalse(any(type(s).__name__=='Ray' for s in w.projectiles))
        self.attack(w,2.2,False)
        self.assertFalse(weapon.locked)
        self.attack(w,.1,True)
        self.assertTrue(any(type(s).__name__=='Ray' for s in w.projectiles))

    def test_glass_quarter_turn_dash_keeps_its_heading_when_movement_is_held(self):
        w=self.world('glasswake')
        pilot=w.component('pilot')
        start=w.player.pos.copy()
        for _ in range(20):pilot.update(w,FIXED_DT,Controls(x=1,special=True))
        self.assertGreater(w.player.pos.y,start.y+45)
        self.assertLess(abs(w.player.pos.x-start.x),2)
        self.assertAlmostEqual(w.player.angle,math.pi/2)

    def test_watered_blooms_chain_and_dry_seeds_are_harmless(self):
        w=self.world('bloom_siege')
        weapon=w.component('weapon')
        module=importlib.import_module(type(weapon).__module__)
        pods=[module.Pod(Vec(x,200),weapon,0) for x in (200,300,400)]
        weapon.active=pods
        w.projectiles=pods.copy()
        for pod in pods:pod.growth=1.
        enemy=self.enemy(w,(470,200))
        pods[0].fuse=0
        self.attack(w,.6,False)
        self.assertLess(enemy.health,1000)
        self.assertTrue(all(p.bloom for p in pods))
        early=module.Pod(Vec(200,200),weapon,0)
        early.fuse=0
        early.update(w,FIXED_DT)
        self.assertFalse(early.alive)
        self.assertFalse(early.bloom)

    def test_echoes_keep_recorded_origins_and_directions_after_player_moves(self):
        w=self.world('echo_vault')
        self.enemy(w,(750,200))
        self.attack(w,FIXED_DT,True)
        shots=[s for s in w.projectiles if type(s).__name__=='Echo']
        self.assertEqual(len(shots),2)
        origin=shots[1].pos.copy()
        velocity=shots[1].vel.copy()
        w.player.pos=Vec(200,350)
        self.attack(w,.3,False)
        self.assertEqual(shots[1].pos,origin)
        self.assertEqual(shots[1].vel,velocity)
        self.attack(w,.6,False)
        self.assertGreater(shots[1].pos.x,origin.x)
        self.assertAlmostEqual(shots[1].pos.y,origin.y)

    def test_rewind_restores_safe_past_position_without_healing_or_repeating_while_held(self):
        w=self.world('echo_vault')
        pilot=w.component('pilot')
        for i in range(240):
            w.time+=FIXED_DT
            pilot.update(w,FIXED_DT,Controls(x=1))
        old=w.player.pos.copy()
        w.player.health=55
        pilot.update(w,0,Controls(special=True))
        self.assertLess(w.player.pos.x,old.x-300)
        self.assertEqual(w.player.health,55)
        rewound=w.player.pos.copy()
        for _ in range(10):pilot.update(w,FIXED_DT,Controls(special=True))
        self.assertEqual(w.player.pos,rewound)
        self.assertGreater(pilot.cooldown,4.)

    def test_bubble_entrains_before_burst_then_damages_once(self):
        w=self.world('tidal_choir')
        weapon=w.component('weapon')
        module=importlib.import_module(type(weapon).__module__)
        bubble=module.Bubble(Vec(300,200),weapon,0)
        bubble.release(w,Vec(1,0),1.)
        bubble.vel=Vec()
        enemy=self.enemy(w,(345,200))
        before=enemy.pos.copy()
        bubble.update(w,.1)
        self.assertLess(enemy.pos.x,before.x)
        self.assertEqual(enemy.health,1000)
        bubble.age=1.34
        bubble.update(w,.02)
        self.assertTrue(bubble.popped)
        self.assertLess(enemy.health,1000)
        after=enemy.health
        bubble.update(w,.02)
        self.assertEqual(enemy.health,after)

    def test_inertia_buoyancy_brake_and_ballast_have_distinct_motion(self):
        scrap=self.world('scrap_ballet')
        pilot=scrap.component('pilot')
        pilot.update(scrap,.3,Controls(x=1))
        before=scrap.player.vel.length()
        pilot.update(scrap,.1,Controls())
        self.assertGreater(scrap.player.vel.x,0)
        pilot.update(scrap,0,Controls(special=True))
        self.assertLess(scrap.player.vel.length(),before*.2)
        tide=self.world('tidal_choir')
        pilot=tide.component('pilot')
        pilot.update(tide,.2,Controls())
        self.assertLess(tide.player.vel.y,0)
        pilot.update(tide,0,Controls(special=True))
        self.assertGreater(tide.player.vel.y,200)

    def test_new_demo_policies_use_only_keyboard_and_dpad_directions(self):
        for pak in NEW:
            w=self.world(pak)
            self.enemy(w,(600,300))
            for position in ((30,30),(450,240),(930,450),(700,400)):
                w.player.pos=Vec(position)
                control=w.component('pilot').demo_controls(w)
                control=w.component('weapon').demo_controls(w,control)
                self.assertIn(control.x,(-1,0,1),(pak,control))
                self.assertIn(control.y,(-1,0,1),(pak,control))

    def test_pulse_mashing_cannot_damage_even_after_many_upgrades(self):
        w=self.world('pulse_abbey')
        w.powerups_collected=100
        enemy=self.enemy(w,(230,200))
        for _ in range(100):
            self.attack(w,.1,True)
            self.attack(w,.1,False)
        self.assertEqual(enemy.health,1000)
        self.assertFalse(any(type(s).__name__=='Resonance' for s in w.projectiles))
        self.attack(w,.45,True)
        self.attack(w,.15,False)
        self.assertLess(enemy.health,1000)

    def test_followup_pulse_starts_compact_grows_with_upgrades_and_penalizes_offbeat(self):
        w=self.world('pulse_abbey')
        module=importlib.import_module(type(w.component('weapon')).__module__)
        fresh=module.Resonance(w.player.pos,1.2,True,0)
        upgraded=module.Resonance(w.player.pos,1.2,True,4)
        offbeat=module.Resonance(w.player.pos,1.2,False,0)
        self.assertLessEqual(fresh.reach,180)
        self.assertGreater(upgraded.reach,fresh.reach+60)
        self.assertLessEqual(offbeat.damage,fresh.damage*.15)
        enemy=self.enemy(w,(420,200))
        for _ in range(100):
            if fresh.alive:fresh.update(w,FIXED_DT)
        self.assertEqual(enemy.health,1000)
        self.assertLessEqual(fresh.radius,fresh.reach)

    def test_followup_nectar_positions_vary_in_both_axes_each_level_and_are_seeded(self):
        for seed in (0,24,997):
            w=self.world('bloom_siege')
            w.seed=seed
            weapon=w.component('weapon')
            before_rng=w.rng.getstate()
            previous=None
            for level in range(1,10):
                w.wave=level
                weapon.build_wells(w)
                positions=[well.position.copy() for well in weapon.wells]
                self.assertGreater(abs(positions[0].y-positions[1].y),70)
                if previous:
                    self.assertTrue(all(min(p.distance_to(old) for old in previous)>70 for p in positions))
                weapon.build_wells(w)
                self.assertEqual(positions,[well.position for well in weapon.wells])
                previous=positions
            self.assertEqual(w.rng.getstate(),before_rng)

    def test_followup_bloom_cannot_sow_inside_or_straddling_a_nectar_pool(self):
        w=self.world('bloom_siege')
        weapon=w.component('weapon')
        weapon.water=4
        center=weapon.wells[0].position.copy()
        for offset in (Vec(),Vec(42,0),Vec(42+w.player.radius-1,0)):
            w.player.pos=center+offset
            self.attack(w,.5,True)
            self.assertFalse(weapon.active)
            self.assertEqual(weapon.water,4)
        w.player.pos=center+Vec(42+w.player.radius+12,0)
        self.attack(w,.5,True)
        self.assertEqual(len(weapon.active),1)
        self.assertGreater(weapon.active[0].growth,0)
        self.assertLess(weapon.water,4)

    def test_followup_tidal_bubbles_rebound_with_energy_loss_at_all_edges_and_corners(self):
        w=self.world('tidal_choir')
        weapon=w.component('weapon')
        module=importlib.import_module(type(weapon).__module__)
        for position,velocity,axes in ((Vec(44,240),Vec(-200,0),(0,)),
                                      (Vec(916,240),Vec(200,0),(0,)),
                                      (Vec(480,44),Vec(0,-200),(1,)),
                                      (Vec(480,436),Vec(0,200),(1,)),
                                      (Vec(44,44),Vec(-200,-200),(0,1))):
            bubble=module.Bubble(position,weapon,0)
            bubble.release(w,Vec(),1.)
            bubble.vel=velocity.copy()
            bubble.update(w,.03)
            self.assertFalse(bubble.popped)
            self.assertTrue(bubble.alive)
            self.assertGreaterEqual(bubble.pos.x,bubble.radius)
            self.assertGreaterEqual(bubble.pos.y,bubble.radius)
            self.assertLessEqual(bubble.pos.x,960-bubble.radius)
            self.assertLessEqual(bubble.pos.y,480-bubble.radius)
            self.assertLess(bubble.vel.length(),velocity.length()*.8)
            for axis in axes:self.assertLess(bubble.vel[axis]*velocity[axis],0)
            bubble.age=1.34
            bubble.update(w,.02)
            self.assertTrue(bubble.popped)  # The fuse still works after a rebound.

    def test_scrap_is_scattered_before_input_and_collecting_cannot_create_ammo(self):
        w=self.world('scrap_ballet')
        weapon=w.component('weapon')
        self.assertGreaterEqual(len(weapon.active),17)
        self.assertTrue(all(s.state=='free' and s.vel.length()>0 for s in weapon.active))
        for piece in weapon.active:
            piece.pos=Vec(800,400)
            piece.vel=Vec()
        count=len(weapon.active)
        self.attack(w,1.,True)
        self.attack(w,.1,False)
        self.assertEqual(len(weapon.active),count)
        self.assertFalse(weapon.orbiters())
        self.assertTrue(all(s.state=='free' for s in weapon.active))

    def test_death_notifications_are_once_only_and_scrap_drops_for_foreign_enemies(self):
        w=self.world('scrap_ballet')
        w.mix['enemy']='signal_runner'
        w.component('enemy')
        calls=[]
        for role in CHANNELS:
            part=w.component(role)
            callback=part.on_enemy_destroyed
            part.on_enemy_destroyed=lambda world,enemy,role=role,callback=callback:(calls.append((role,world.kills,enemy.id)),callback(world,enemy))
        weapon=w.component('weapon')
        before=len(weapon.active)
        enemy=self.enemy(w,(400,300))
        enemy.health=0
        w.remove_dead()
        w.remove_dead()
        self.assertEqual(len(weapon.active),before+3)
        self.assertEqual({c[0] for c in calls},set(CHANNELS))
        self.assertEqual(len(calls),6)
        self.assertTrue(all(c[1:]==(1,enemy.id) for c in calls))
        self.enemy(w)
        w.enemies.clear()  # A despawn is not a kill.
        w.remove_dead()
        self.assertEqual(len(calls),6)

    def test_nectar_refills_only_while_stationary_and_growth_spends_the_can(self):
        w=self.world('bloom_siege')
        weapon=w.component('weapon')
        w.player.pos=weapon.wells[0].position.copy()
        weapon.update(w,1.,Controls(x=1))
        self.assertEqual(weapon.water,0)
        w.player.vel=Vec(30,0)
        weapon.update(w,1.,Controls())
        self.assertEqual(weapon.water,0)
        w.player.vel=Vec()
        weapon.update(w,1.,Controls())
        self.assertEqual(weapon.water,2)
        w.player.pos+=Vec(70,0)  # Leave the refill pool before sowing.
        self.attack(w,.8,True)
        plant=weapon.active[0]
        self.assertAlmostEqual(plant.growth+weapon.water,2)
        self.assertGreater(plant.growth,.6)
        growth=plant.growth
        plant.update(w,2.)
        self.assertEqual(plant.growth,growth)
        weapon.water=0
        self.attack(w,.2,True)
        self.assertEqual(plant.growth,growth)

    def test_nectar_capacity_upgrades_preserve_water_and_owned_wells_cleanup(self):
        w=self.world('bloom_siege')
        weapon=w.component('weapon')
        self.assertEqual(weapon.capacity(w),4)
        weapon.water=2
        w.powerups_collected=5
        weapon.on_powerup(w,5)
        self.assertEqual(weapon.capacity(w),14)
        self.assertEqual(weapon.water,2)
        w.start_wave()
        self.assertEqual(weapon.water,2)
        w.mix['obstacles']='iron_circuit'
        w.cover=w.component('obstacles').build(w)
        weapon.on_shuffle(w,frozenset({'obstacles'}))
        wells=list(weapon.wells)
        self.assertTrue(all(s in w.geometry and not s.blocks_body(w.player) for s in wells))
        w.mix['weapon']='signal_runner'
        w.component('weapon')
        self.assertTrue(all(s not in w.geometry for s in wells))

    def test_small_bubbles_never_pull_or_damage_even_with_upgrades(self):
        for charge in (0,.1,.59,.6):
            w=self.world('tidal_choir')
            weapon=w.component('weapon')
            module=importlib.import_module(type(weapon).__module__)
            bubble=module.Bubble(Vec(300,200),weapon,100)
            bubble.release(w,Vec(),charge)
            enemy=self.enemy(w,(320,200))
            before=enemy.pos.copy()
            bubble.update(w,.1)
            if charge<.6:
                self.assertFalse(bubble.powered)
                self.assertEqual(enemy.pos,before)
                bubble.age=1.4
                bubble.update(w,.01)
                self.assertEqual(enemy.health,1000)
            else:
                self.assertTrue(bubble.powered)
                self.assertNotEqual(enemy.pos,before)

    def test_glass_bolts_reflect_borders_mirrors_and_respect_projectile_filtering(self):
        w=self.world('glasswake')
        module=importlib.import_module(type(w.component('enemy')).__module__+'.hazards')
        # Enemy module imports its helpers; use the real class, not a mock shot.
        for position,velocity,axis in ((Vec(950,100),Vec(300,0),0),(Vec(500,470),Vec(0,300),1)):
            bolt=module.Bolt(position,velocity,10)
            bolt.update(w,.1)
            self.assertTrue(bolt.alive)
            self.assertLess(bolt.vel[axis],0)
        w.cover=[Cover(pygame.Rect(400,80,2,80),100,100)]
        bolt=module.Bolt(Vec(300,100),Vec(1000,0),10)
        bolt.update(w,.2)
        self.assertTrue(bolt.alive)
        self.assertLess(bolt.vel.x,0)
        self.assertLess(bolt.pos.x,400)
        class Rail(Cover):
            def blocks_projectile(self,shot):return False
        w.cover=[Rail(pygame.Rect(400,80,2,80),100,100)]
        bolt=module.Bolt(Vec(300,100),Vec(1000,0),10)
        bolt.update(w,.2)
        self.assertGreater(bolt.pos.x,400)
        self.assertGreater(bolt.vel.x,0)
        bolt.update(w,6.)
        self.assertFalse(bolt.alive)

    def test_glass_banked_beam_damage_triples_at_each_reflection(self):
        w=self.world('glasswake')
        w.prefs.aim_assist=False
        weapon=w.component('weapon')
        module=importlib.import_module(type(weapon).__module__)
        weapon.aim=lambda world:Vec(1,1).normalize()
        w.player.pos=Vec(200,100)
        enemies=[self.enemy(w,p) for p in ((300,200),(650,406),(900,40))]
        # Isolate the weapon's reflection formula from the skater's shield policy.
        w.hit_enemy=lambda enemy,damage:w.apply_damage(enemy,damage)
        ray=module.Ray(weapon)
        ray.update(w,.1)
        damage=[1000-e.health for e in enemies]
        self.assertAlmostEqual(damage[1],damage[0]*3)
        self.assertAlmostEqual(damage[2],damage[0]*9)

    def test_enemy_windups_lock_targets_and_shields_have_vulnerability_windows(self):
        for pak in ('pulse_abbey','bloom_siege','tidal_choir'):
            w=self.world(pak)
            e=self.enemy(w,(500,200))
            part=w.component('enemy')
            e.timer=0
            part.advance_enemy(w,e,FIXED_DT)
            self.assertEqual(e.state,'windup')
            target=e.target.copy()
            w.player.pos=Vec(200,400)
            part.advance_enemy(w,e,.2)
            self.assertEqual(e.target,target)
        w=self.world('glasswake')
        e=self.enemy(w)
        e.state='shield'
        shield=w.hit_enemy(e,10)
        e.state='recover'
        exposed=w.hit_enemy(e,10)
        self.assertGreater(exposed,shield*4)

    def test_animation_rendering_is_read_only_and_all_frames_have_visible_alpha(self):
        pygame.init()
        pygame.display.set_mode((1,1))
        from system_panic.graphics import Graphics
        graphics=Graphics()
        surface=pygame.Surface((960,480))
        try:
            for pak in NEW:
                w=self.world(pak)
                self.enemy(w)
                w.cover=w.component('obstacles').build(w)
                self.attack(w,.4,True)
                before=(w.time,w.rng.getstate(),w.player.pos.copy(),[(e.pos.copy(),e.health) for e in w.enemies])
                graphics.draw_world(surface,w)
                graphics.draw_world(surface,w)
                self.assertEqual(before,(w.time,w.rng.getstate(),w.player.pos,[(e.pos,e.health) for e in w.enemies]))
                for role in ('pilot','enemy','weapon','obstacles'):
                    art=next(h for h in w.component(role)._assets.handles.values() if hasattr(h,'surface'))
                    metadata=json.loads((ROOT/'paks'/pak/'pak.json').read_text())
                    columns,rows=metadata['authoring'].get('component_grids',{}).get(role,[4,1])
                    for index in range(4):
                        frame=art.frame(index*columns if rows==4 else index,columns=columns,rows=rows)
                        self.assertGreater(pygame.mask.from_surface(art.surface.subsurface(frame.rect)).count(),100)
        finally:
            pygame.quit()

    def test_glass_skater_demo_routes_past_mirrors_instead_of_stalling_after_level_one(self):
        from system_panic.app import autopilot
        for seed in (0,24):
            w=World(Preferences(difficulty='relaxed'),seed,solo='glasswake')
            self.addCleanup(w.close)
            for _ in range(90*60):
                w.advance(1/60,autopilot(w))
                if w.wave>2 or w.phase=='dead':break
            self.assertGreater(w.wave,2,(seed,w.wave,w.phase,w.player.health))


if __name__=='__main__':unittest.main()
