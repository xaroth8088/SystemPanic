"""Player feedback: clean presentation, physical alignment and revised danger."""
import ast
import hashlib
import importlib
import math
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import pygame
from system_panic.model import Controls,Vec,FIXED_DT,Cover
from system_panic.pak_assets import ImageAsset
from system_panic.preferences import Preferences
from system_panic.world import World
from system_panic.graphics import Graphics

class ArcadeFeedbackTests(unittest.TestCase):
    def world(self,pak,terrain=False):
        w=World(Preferences(),24,solo=pak);self.addCleanup(w.close);w.phase='active';w.enemies.clear()
        if not terrain:w.cover=[]
        w.player.pos=Vec(200,200);w.player.invulnerable=0
        return w
    def graphics(self):
        pygame.init();pygame.display.set_mode((1,1));self.addCleanup(pygame.quit)
        return Graphics()
    def module(self,part,name):return importlib.import_module(type(part).__module__+'.'+name)
    def test_three_pilots_restore_original_single_pose_with_rotation(self):
        hashes={'orbit_keeper':'99bd6d11c1ba11ebcdc54d1ba2adc31ea33eca94b90a82955e57a7121c9a56ba','void_drifter':'7a3fdafbe252fcd4de9dfcba7fa1888cb1fadecd3887fe66ac41bed89603aa3e','iron_circuit':'2282d96c27f12ca1ffab5a0739e8685f67c4068e8f15d3dd922e03a5fdc4337e'}
        for pak,digest in hashes.items():
            w=self.world(pak);part=w.component('pilot')
            self.assertEqual(hashlib.sha256((ROOT/f'paks/{pak}/pilot/pilot_sheet.png').read_bytes()).hexdigest(),digest)
            self.assertIsInstance(part.sprite(w),ImageAsset)
            w.player.angle=0;self.assertEqual(part.sprite_angle(w,w.player),-90)
            w.player.angle=math.pi;self.assertEqual(part.sprite_angle(w,w.player),-270)
    def test_shared_renderer_has_no_direction_tick(self):
        w=self.world('signal_runner');g=self.graphics();w.component('background').draw=lambda s,w:s.fill((0,0,0))
        with patch.object(pygame.draw,'line') as line:g.draw_world(pygame.Surface((960,480)),w)
        line.assert_not_called()
    def test_control_instruction_prose_is_not_drawn_by_weapons(self):
        for file in (ROOT/'paks').glob('*/weapon/*.py'):
            text=file.read_text(encoding='utf-8');tree=ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='graphics' and node.func.attr=='text':
                    self.assertIn('NECTAR {w.water',ast.get_source_segment(text,node),str(file))
    def test_sky_pilot_and_enemy_feet_reach_the_actual_floor(self):
        w=self.world('sky_forge');pilot=w.component('pilot');part=w.component('enemy');enemy=w.spawn_enemy(Vec(400,100));enemy.timer=100
        for _ in range(240):pilot.update(w,FIXED_DT,Controls());part.advance_enemy(w,enemy,FIXED_DT)
        self.assertAlmostEqual(w.player.pos.y+w.player.radius,480)
        self.assertAlmostEqual(enemy.pos.y+enemy.radius,480)
        g=self.graphics()
        for channel,body,size in (('pilot',w.player,44),('enemy',enemy,int(enemy.radius*3.4))):
            surface=pygame.Surface((960,480),pygame.SRCALPHA)
            if channel=='pilot':pilot.draw(g,surface,w,reduced_motion=True)
            else:part.draw(g,surface,w,enemy,reduced_motion=True)
            visible=surface.get_bounding_rect(min_alpha=110)
            self.assertGreaterEqual(visible.bottom,479,(channel,visible))
            self.assertLessEqual(visible.bottom,480,(channel,visible))
    def test_sword_sweeps_overhead_and_pushes_once_on_both_facings(self):
        for facing in (-1,1):
            w=self.world('sky_forge');weapon=w.component('weapon');m=self.module(weapon,'projectile')
            enemies=[w.spawn_enemy(Vec(200+facing*x,200+y)) for x,y in ((30,-45),(50,5))]
            for e in enemies:e.health=e.max_health=1000
            before=[e.pos.copy() for e in enemies];swing=m.Swing(w,weapon,Vec(facing,0))
            for _ in range(28):swing.update(w,FIXED_DT)
            for e,start in zip(enemies,before):
                self.assertEqual(e.health,1000-swing._damage)
                self.assertGreater(e.pos.distance_to(start),20)
            self.assertFalse(swing.alive)
    def test_dropped_sword_has_no_direction_arrow(self):
        w=self.world('sky_forge');weapon=w.component('weapon');weapon.fire(w,Vec(1,0),1.3)
        readout=self.module(weapon,'readout').Readout(weapon);g=self.graphics()
        with patch.object(pygame.draw,'line') as line:readout.draw(g,pygame.Surface((960,480)),w)
        line.assert_not_called()
    def test_sword_demo_walks_fully_off_an_overhung_deck_to_recover_a_lower_blade(self):
        w=self.world('sky_forge');pilot=w.component('pilot');weapon=w.component('weapon')
        w.cover=[Cover(pygame.Rect(107,380,144,16),36,36)]
        w.player.pos=Vec(87,358);w.player.vel=Vec();pilot._grounded=True
        weapon.fire(w,Vec(1,0),1.3);sword=weapon._sword;sword.pos=Vec(99,473);sword.drop()
        for _ in range(360):
            w.time+=FIXED_DT
            control=weapon.demo_controls(w,Controls())
            pilot.update(w,FIXED_DT,control);weapon.update(w,FIXED_DT,control);w.update_projectiles(FIXED_DT)
            if weapon._sword is None:break
        self.assertIsNone(weapon._sword)
    def test_orbit_obstacles_ignore_arbitrary_damage(self):
        w=self.world('orbit_keeper',True)
        for wall in w.cover:
            before=wall.health;self.assertEqual(w.hit_cover(wall,10000),0);self.assertEqual(wall.health,before)
    def test_neon_paddle_has_wide_flat_footprint_on_every_edge(self):
        w=self.world('neon_breach');pilot=w.component('pilot');g=self.graphics()
        width,height=936,456
        for edge,distance in enumerate((width/2,width+height/2,width+height+width/2,2*width+height+height/2)):
            pilot._distance=distance;pilot.move(w,0,Controls(),False)
            rect=w.player.footprint();self.assertEqual(w.player.edge,edge)
            surface=pygame.Surface((960,480),pygame.SRCALPHA);pilot.draw(g,surface,w,reduced_motion=True)
            box=surface.get_bounding_rect(min_alpha=32)
            if edge==0:self.assertEqual(box.top,0);self.assertEqual(rect.top,0)
            if edge==1:self.assertEqual(box.right,960);self.assertEqual(rect.right,960)
            if edge==2:self.assertEqual(box.bottom,480);self.assertEqual(rect.bottom,480)
            if edge==3:self.assertEqual(box.left,0);self.assertEqual(rect.left,0)
            self.assertEqual(max(rect.size),84)
    def test_wide_neon_paddle_returns_balls_at_its_outer_span_on_all_sides(self):
        for edge,distance in enumerate((468,1164,1860,2556)):
            w=self.world('neon_breach');pilot=w.component('pilot');pilot._distance=distance;pilot.move(w,0,Controls(),False)
            weapon=w.component('weapon');m=self.module(weapon,'projectile');inward=Vec(math.cos(w.player.angle),math.sin(w.player.angle));tangent=Vec(-inward.y,inward.x)
            ball=m.PlasmaBall(w,weapon,inward);ball.pos=w.player.pos+tangent*36+inward*18;ball.vel=-inward*420
            ball.update(w,FIXED_DT)
            self.assertEqual(weapon.returns,1,edge);self.assertGreater(ball.vel.dot(inward),0)
    def test_maze_exits_vary_and_no_center_through_line_is_forced(self):
        rows=set()
        for seed in range(8):
            w=self.world('maze_muncher');w.seed=seed;o=w.component('obstacles')
            for level in (1,2,7):
                w.wave=level;before=w.rng.getstate();w.cover=o.build(w);row=o._exit_row;rows.add(row)
                self.assertEqual(before,w.rng.getstate())
                route=self.module(w.component('pilot'),'navigation').Route();route.direction(w,Vec(480,240))
                self.assertIn((29,row),route.links[(0,row)])
                self.assertTrue(any(c.overlaps_circle(Vec(x,240),1) for c in w.cover for x in range(48,920,32)))
                start=next(iter(route.nodes));visited={start};queue=[start]
                while queue:
                    for node in route.links[queue.pop()]:
                        if node not in visited:visited.add(node);queue.append(node)
                self.assertEqual(visited,set(route.nodes))
        self.assertGreaterEqual(len(rows),5)
    def test_burrow_rush_starts_immediately_after_emerging_without_cues(self):
        w=self.world('burrow_patrol');part=w.component('enemy');enemy=w.spawn_enemy(Vec(400,200));enemy.timer=0
        part.advance_enemy(w,enemy,FIXED_DT);self.assertEqual(enemy.state,'burrow')
        part.advance_enemy(w,enemy,.91);self.assertEqual(enemy.state,'rush')
        self.assertGreater(enemy.vel.length(),part.move_speed(w)*2)
        self.assertFalse(w.projectiles)
    def test_vector_pauses_then_darts_in_a_seeded_random_direction_and_hits_hard(self):
        w=self.world('vector_coil');part=w.component('enemy');enemy=w.spawn_enemy(Vec(400,200));enemy.timer=0
        start=enemy.pos.copy();part.advance_enemy(w,enemy,FIXED_DT)
        self.assertEqual(enemy.state,'pause');self.assertEqual(enemy.pos,start)
        while enemy.state=='pause':part.advance_enemy(w,enemy,FIXED_DT)
        self.assertEqual(enemy.state,'dart');self.assertGreater(enemy.vel.length(),part.move_speed(w)*3)
        self.assertGreaterEqual(part.contact_damage(w),30)
        part.on_contact(w,enemy,FIXED_DT);self.assertLessEqual(w.player.health,70)
    def test_star_volley_is_spread_near_player_with_more_shots(self):
        w=self.world('star_bastion');part=w.component('enemy');enemy=w.spawn_enemy(Vec(400,60));w.player.pos=Vec(480,440)
        targets=set()
        for _ in range(20):
            w.projectiles.clear();enemy.state='formation';enemy.timer=0
            part.advance_enemy(w,enemy,FIXED_DT);targets.add(tuple(enemy.target))
            self.assertGreaterEqual(len(w.projectiles),3)
            self.assertLessEqual(abs(enemy.target.x-w.player.pos.x),95)
            self.assertLessEqual(abs(enemy.target.y-w.player.pos.y),28)
        self.assertGreater(len(targets),15)
        self.assertLess(part.fire_interval(w),2)
    def test_tide_hops_grant_no_movement_iframes_or_protection_circle(self):
        w=self.world('tide_hopper');pilot=w.component('pilot')
        for special in (False,True):
            pilot._landing=None;pilot._hop_remaining=0
            pilot.update(w,FIXED_DT,Controls(x=1,special=special));self.assertEqual(w.player.invulnerable,0)
        w.player.invulnerable=.5;g=self.graphics()
        with patch.object(pygame.draw,'circle') as circle:pilot.draw(g,pygame.Surface((960,480)),w,reduced_motion=True)
        circle.assert_not_called()
    def test_bloom_damage_rewards_maturity_non_linearly_with_smaller_radii(self):
        w=self.world('bloom_siege');weapon=w.component('weapon');m=importlib.import_module(type(weapon).__module__)
        values=[]
        for growth in (.25,.5,1.):
            pod=m.Pod(Vec(300,200),weapon);pod.growth=growth;pod.fuse=0;pod.update(w,0)
            values.append((pod.damage,pod.radius))
        self.assertGreater(values[2][0]-values[1][0],3*(values[1][0]-values[0][0]))
        self.assertLessEqual(values[2][1],100)
        self.assertGreater(values[2][0],100)

if __name__=='__main__':unittest.main()
