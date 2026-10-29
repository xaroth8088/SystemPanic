"""Specific player feedback: physical behavior, reused boundaries and useful art."""
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import pygame
from system_panic.model import Vec,Controls,Cover,FIXED_DT
from system_panic.preferences import Preferences
from system_panic.world import World

class PlaytestRefinementTests(unittest.TestCase):
    def world(self,pak,empty=True):
        w=World(Preferences(),24,solo=pak);self.addCleanup(w.close)
        w.phase='active';w.enemies.clear()
        if empty:w.cover=[]
        w.player.pos=Vec(200,200)
        return w
    def module(self,part,name):return importlib.import_module(type(part).__module__+'.'+name)
    def test_black_hole_center_is_escapable_with_ordinary_thrust(self):
        for offset in (0,1,20,60):
            w=self.world('void_drifter');o=w.component('obstacles');p=w.component('pilot')
            hole=o.holes[0];w.cover=[hole];o._next_comet=1000
            w.player.pos=hole.pos+Vec(offset,0);w.player.vel=Vec();w.player.angle=0
            for _ in range(240):
                w.time+=FIXED_DT;p.update(w,FIXED_DT,Controls(y=-1));o.update(w,FIXED_DT)
            self.assertGreater(w.player.pos.distance_to(hole.pos),hole.influence)
            self.assertGreater(w.player.health,0)
    def test_car_heading_survives_wall_hits_and_speed_depends_on_actual_motion(self):
        w=self.world('iron_circuit');p=w.component('pilot');w.player.angle=0
        w.player.pos=Vec(275,200);w.cover=[Cover(pygame.Rect(300,0,20,480),100,100)]
        for _ in range(180):p.update(w,FIXED_DT,Controls())
        self.assertEqual(w.player.angle,0)
        self.assertLess(w.player.vel.length(),1)
        self.assertLess(p._speed,70)
        p.update(w,FIXED_DT,Controls(x=1))
        self.assertGreater(w.player.angle,0)
    def test_car_accelerates_automatically_and_obeys_both_top_speeds(self):
        w=self.world('iron_circuit');p=w.component('pilot');w.player.angle=0
        speeds=[]
        for _ in range(600):
            w.player.pos=Vec(200,200);p.update(w,FIXED_DT,Controls());speeds.append(w.player.vel.length())
        self.assertGreater(speeds[-1],speeds[0]*3)
        self.assertAlmostEqual(max(speeds),340,places=5)
        p._speed=425;p._dash_remaining=.4
        p.update(w,FIXED_DT,Controls())
        self.assertLessEqual(w.player.vel.length(),430.0001)
        p._dash_remaining=0;p.update(w,FIXED_DT,Controls())
        self.assertLessEqual(w.player.vel.length(),340.0001)
    def test_sword_only_throws_on_charged_release_and_cannot_attack_until_collected(self):
        w=self.world('sky_forge');weapon=w.component('weapon')
        for _ in range(80):weapon.update(w,FIXED_DT,Controls(fire=True))
        self.assertIsNone(weapon._sword)
        weapon.update(w,FIXED_DT,Controls())
        sword=weapon._sword;self.assertIsNotNone(sword)
        for _ in range(180):weapon.update(w,FIXED_DT,Controls(fire=_%2==0))
        self.assertEqual(sum(type(s).__name__ in ('Sword','Swing') for s in w.projectiles),1)
        sword.pos=Vec(600,200);sword.drop();sword.update(w,1.)
        self.assertIs(weapon._sword,sword)
        sword.pos=w.player.pos.copy();sword.pickup_lock=0;sword.update(w,0)
        self.assertIsNone(weapon._sword)
        self.assertEqual(w.powerups_collected,0)
    def test_sword_survives_projectile_clears_and_level_rebuilds_as_unclaimed(self):
        w=self.world('sky_forge');weapon=w.component('weapon')
        weapon.fire(w,Vec(1,0),1.3);sword=weapon._sword
        w.projectiles.clear();weapon.on_shuffle(w,{'music'});weapon.update(w,FIXED_DT,Controls())
        self.assertIn(sword,w.projectiles)
        w.projectiles.clear();w.cover=[Cover(pygame.Rect(200,100,100,200),1,1)]
        weapon.on_level_start(w);weapon.update(w,FIXED_DT,Controls())
        self.assertIn(sword,w.projectiles);self.assertEqual(sword.state,'resting')
        self.assertFalse(any(c.overlaps_circle(sword.pos,sword.radius) for c in w.cover))
        sword.pos=Vec(250,200);weapon.on_shuffle(w,{'obstacles'})
        self.assertFalse(any(c.overlaps_circle(sword.pos,sword.radius) for c in w.cover))
        self.assertIs(weapon._sword,sword)
    def test_sword_stab_and_flight_respect_filtered_obstacles(self):
        w=self.world('sky_forge');weapon=w.component('weapon');m=self.module(weapon,'projectile')
        foe=w.spawn_enemy(Vec(290,200));foe.health=foe.max_health=1000
        w.cover=[Cover(pygame.Rect(235,170,20,60),1000,1000)]
        stab=m.Swing(w,weapon,Vec(1,0));stab.update(w,FIXED_DT)
        self.assertEqual(foe.health,1000)
        sword=m.Sword(w,weapon,Vec(1,0),1);sword.update(w,.2)
        self.assertEqual(sword.state,'resting');self.assertEqual(foe.health,1000)
        self.assertLess(sword.pos.x,235)
    def test_phase_readout_does_not_draw_or_reveal_attack_radius(self):
        w=self.world('phase_garden');weapon=w.component('weapon');m=self.module(weapon,'readout')
        from system_panic.graphics import Graphics
        pygame.init();pygame.display.set_mode((1,1));self.addCleanup(pygame.quit)
        with patch.object(pygame.draw,'circle') as circle,patch.object(Graphics,'text') as text:
            m.Readout(weapon).draw(Graphics(),pygame.Surface((960,480)),w)
        circle.assert_not_called()
        self.assertFalse(any('RANGE' in str(c) or 'REACH' in str(c) for c in text.call_args_list))
    def test_maze_is_connected_seeded_and_has_both_wrap_links(self):
        signatures=[]
        for level in (1,2,7):
            w=self.world('maze_muncher',False);w.wave=level;o=w.component('obstacles')
            before=w.rng.getstate();w.cover=o.build(w)
            signatures.append(tuple(tuple(s.rect) for s in w.cover));self.assertEqual(before,w.rng.getstate())
            route=self.module(w.component('pilot'),'navigation').Route()
            route.direction(w,Vec(50,240));nodes=route.nodes
            start=next(iter(nodes));visited={start};queue=[start]
            while queue:
                for node in route.links[queue.pop()]:
                    if node not in visited:visited.add(node);queue.append(node)
            self.assertEqual(visited,set(nodes))
            row=o._exit_row
            self.assertIn((29,row),route.links[(0,row)])
            self.assertIn((0,row),route.links[(29,row)])
            self.assertGreater(len(w.cover),20)
        self.assertEqual(len(set(signatures)),3)
    def test_maze_pilot_enemy_and_bite_share_horizontal_wrap(self):
        w=self.world('maze_muncher',False);pilot=w.component('pilot')
        y=16+32*w.component('obstacles')._exit_row
        w.player.pos=Vec(1,y);pilot._direction=pilot._wanted=Vec(-1,0)
        pilot.update(w,.02,Controls(x=-1));self.assertGreater(w.player.pos.x,950)
        w.player.pos=Vec(959,y);pilot._direction=pilot._wanted=Vec(1,0)
        pilot.update(w,.02,Controls(x=1));self.assertLess(w.player.pos.x,10)
        part=w.component('enemy');enemy=w.spawn_enemy(Vec(959,y));enemy.pos=Vec(959,y);enemy.stunned=1;enemy.vel=Vec(200,0)
        part.advance_enemy(w,enemy,.03);self.assertLess(enemy.pos.x,10)
        enemy.pos=Vec(955,y);enemy.health=enemy.max_health=1000
        w.player.pos=Vec(5,y);w.player.angle=math.pi
        w.component('weapon').update(w,FIXED_DT,Controls(fire=True))
        self.assertLess(enemy.health,1000)
    def test_maze_routes_realign_displaced_bodies_before_extending_a_corridor(self):
        w=self.world('maze_muncher');part=w.component('pilot');module=self.module(part,'navigation')
        route=module.Route()
        self.assertEqual(route.vector(Vec(25,5)),Vec(0,1))
        self.assertEqual(route.vector(Vec(5,22)),Vec(1,0))
        self.assertEqual(route.vector(Vec()),Vec())
        w.player.pos=Vec(76,299)
        part._direction=Vec(1,0)
        for _ in range(240):
            direction=route.direction(w,Vec(200,304))
            part.update(w,FIXED_DT,Controls(direction.x,direction.y))
        self.assertGreater(w.player.pos.x,190)
        self.assertAlmostEqual(w.player.pos.y,304,delta=4)
    def draw_path(self,w,points):
        weapon=w.component('weapon')
        for point in points:
            w.player.pos=Vec(point);weapon.update(w,FIXED_DT,Controls(fire=True))
    def test_vector_new_three_sides_close_against_an_old_box_edge(self):
        w=self.world('vector_coil');weapon=w.component('weapon')
        self.draw_path(w,[(200,200),(320,200),(320,320),(200,320),(200,190)])
        self.assertEqual(len(weapon._areas),1)
        weapon.update(w,FIXED_DT,Controls())
        foe=w.spawn_enemy(Vec(380,250));foe.health=foe.max_health=1000
        self.draw_path(w,[(320,200),(440,200),(440,320),(320,320)])
        self.assertEqual(len(weapon._areas),2)
        self.assertEqual(foe.health,0)
    def test_vector_connected_box_network_routes_but_disconnected_boxes_do_not(self):
        w=self.world('vector_coil');weapon=w.component('weapon');m=self.module(weapon,'network');g=self.module(weapon,'geometry')
        boxes=[g.CarvedArea([Vec(x,y) for x,y in points],(1,2,3)) for points in (
            [(100,100),(200,100),(200,200),(100,200)],[(200,100),(300,100),(300,200),(200,200)])]
        polygon=m.close([Vec(100,100),Vec(100,50),Vec(300,50)],Vec(300,100),boxes)
        self.assertIsNotNone(polygon)
        boxes[1]=g.CarvedArea([Vec(400,100),Vec(500,100),Vec(500,200),Vec(400,200)],(1,2,3))
        self.assertIsNone(m.close([Vec(100,100),Vec(100,50),Vec(400,50)],Vec(400,100),boxes))
        self.assertIsNone(m.close([Vec(100,100),Vec(200,100)],Vec(200,200),boxes))
    def test_star_cover_erodes_one_cell_at_a_time_from_hostile_shots(self):
        w=self.world('star_bastion',False);part=w.component('enemy');m=self.module(part,'bullet')
        cells=w.cover;self.assertGreater(len(cells),50)
        self.assertTrue(all(s.rect.size==(16,16) for s in cells))
        cell=min(cells,key=lambda s:s.rect.top)
        before=[s.health for s in cells]
        shot=m.HostileShot(Vec(cell.rect.centerx,cell.rect.top-5),Vec(0,100),30)
        shot.update(w,.01)
        self.assertFalse(shot.alive)
        self.assertEqual(sum(s.health!=h for s,h in zip(cells,before)),1)
        self.assertEqual(cell.health,0)
    def test_tide_pilot_and_traffic_land_on_the_same_48_pixel_centers(self):
        w=self.world('tide_hopper');pilot=w.component('pilot');enemy=w.spawn_enemy(Vec(24,216))
        w.player.pos=Vec(216,216);pilot.on_level_start(w)
        pilot.update(w,FIXED_DT,Controls(x=1))
        for _ in range(20):pilot.update(w,FIXED_DT,Controls())
        self.assertEqual(w.player.pos,Vec(264,216))
        self.assertIsNone(pilot._landing)
        pilot._hop_remaining=0;pilot.update(w,FIXED_DT,Controls(x=1,special=True))
        for _ in range(35):pilot.update(w,FIXED_DT,Controls())
        self.assertEqual(w.player.pos,Vec(360,216))
        part=w.component('enemy');enemy.timer=0
        paused=False
        for _ in range(200):
            part.advance_enemy(w,enemy,FIXED_DT)
            if enemy.landing is None:
                paused=True
                self.assertAlmostEqual((enemy.pos.x-24)%48,0)
                self.assertAlmostEqual((enemy.pos.y-24)%48,0)
        self.assertTrue(paused)
    def test_tide_external_tow_is_not_undone_by_grid_movement(self):
        w=self.world('tide_hopper');part=w.component('enemy');enemy=w.spawn_enemy(Vec(120,216))
        part.advance_enemy(w,enemy,FIXED_DT)
        for _ in range(30):
            enemy.pos+=Vec(-1,.3);expected=enemy.pos.copy()
            part.advance_enemy(w,enemy,FIXED_DT)
            self.assertEqual(enemy.pos,expected)
            self.assertIsNone(enemy.landing)
    def test_grid_placement_uses_clear_nodes_without_mutating_recovery_geometry(self):
        for pak in ('maze_muncher','tide_hopper'):
            w=self.world(pak,False)
            for role in ('pilot','enemy'):
                module=self.module(w.component(role),'navigation' if pak=='maze_muncher' else 'grid')
                with patch.object(w,'safe_position',side_effect=AssertionError('unneeded recovery may remove geometry')):
                    result=module.grid_position(w,Vec(0,0),w.player) if pak=='maze_muncher' else module.nearest(w,w.player,Vec(0,0))
                self.assertFalse(any(s.blocks_body(w.player) and s.overlaps_circle(result,w.player.radius) for s in w.geometry))
    def test_facing_sheets_have_only_supported_bearings_and_upright_selection(self):
        plan=json.loads((ROOT/'tools/assetforge/facing-prompts.json').read_text(encoding='utf-8-sig'))
        for job in plan['jobs']:
            if job.get('role','pilot')!='pilot' or job['pak'] in ('void_drifter','iron_circuit'):continue
            w=self.world(job['pak']);part=w.component('pilot');columns=job['columns']
            self.assertEqual(columns,2 if job['pak']=='sky_forge' else 4 if job['pak'] in ('maze_muncher','vector_coil','tide_hopper','neon_breach','burrow_patrol') else 8)
            hashes=set()
            for face in range(columns):
                w.player.angle=face*math.tau/columns
                if job['pak']=='neon_breach':
                    w.player.edge=(3,0,1,2)[face]
                    w.player.pos=Vec([(12,240),(480,12),(948,240),(480,468)][face])
                frame=part.sprite(w,w.player);art=frame.image.surface
                pixels=art.subsurface(frame.rect)
                self.assertGreater(pygame.mask.from_surface(pixels,110).count(),100)
                self.assertEqual(part.sprite_angle(w,w.player),0)
                self.assertFalse(part.sprite_flip_x(w,w.player))
                hashes.add(hashlib.sha256(pygame.image.tobytes(pixels,'RGBA')).hexdigest())
            self.assertEqual(len(hashes),columns)
    def test_neon_loop_omits_fade_and_retains_energy_around_the_whole_join(self):
        import numpy as np
        import soundfile as sf
        data,sr=sf.read(ROOT/'paks/neon_breach/music/music.ogg',always_2d=True)
        rms=lambda d:float(np.sqrt(np.mean(d*d)))
        interior=rms(data[sr:-sr]);join=np.concatenate((data[-2*sr:],data[:2*sr]))
        energy=[rms(join[i:i+sr//10]) for i in range(0,len(join)-sr//10,sr//100)]
        self.assertGreater(min(energy),interior*.3)
        self.assertLess(len(data)/sr,21)
    def test_row_exporters_preserve_role_facing_overrides_and_their_provenance(self):
        from tools.assetforge import export_renewal,export_frontier
        with tempfile.TemporaryDirectory(dir=ROOT/'output') as directory:
            root=Path(directory);(root/'assets/images').mkdir(parents=True);(root/'tools/assetforge').mkdir(parents=True)
            (root/'output').mkdir();folder=root/'paks/probe';folder.mkdir(parents=True)
            meta=dict(id='probe',authoring=dict(component_sources=dict(pilot='new-faces.png',weapon='new-sword.png')))
            (folder/'pak.json').write_text(json.dumps(meta))
            atlas=pygame.Surface((256,256),pygame.SRCALPHA);atlas.fill((120,100,80,255))
            pygame.image.save(atlas,root/'assets/images/probe-source.png')
            plan=dict(jobs=[dict(id='probe',file='assets/images/probe-source.png',prompt='fixture')])
            (root/'tools/assetforge/renewal-prompts.json').write_text(json.dumps(plan))
            (root/'tools/assetforge/image-prompts.json').write_text(json.dumps(dict(jobs=[])))
            kept=[]
            for role in ('pilot','enemy','weapon','obstacles','background','music'):(folder/role).mkdir()
            for role in ('pilot','weapon'):
                path=folder/role/(role+'_sheet.png');path.write_bytes(b'preserve exact custom frames')
                kept.append(dict(file=path.relative_to(root).as_posix(),operation='custom facing source'))
            (root/'assets/pak-exports.json').write_text(json.dumps(kept))
            production=root/'assets/audio/production';production.mkdir(parents=True)
            for suffix in ('','_shot','_special'):(production/f'probe{suffix}.ogg').write_bytes(b'audio fixture')
            for exporter in (export_renewal,export_frontier):
                with patch.object(exporter,'ROOT',root),patch.object(sys,'argv',['export']),patch.object(export_frontier,'PAKS',('probe',)):
                    exporter.main()
                records=json.loads((root/'assets/pak-exports.json').read_text())
                for entry in kept:
                    self.assertEqual((root/entry['file']).read_bytes(),b'preserve exact custom frames')
                    self.assertIn(entry,records)

if __name__=='__main__':unittest.main()
