"""Shape-preserving tail routing and quiet visual feedback."""
import importlib
import json
import math
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT))
import pygame
from system_panic.model import Controls,Cover,Enemy,Vec,FIXED_DT
from system_panic.paks import get_catalog
from system_panic.preferences import Preferences
from system_panic.world import World
from tools.assetforge.export_facings import source_cells


class VisualCleanupTests(unittest.TestCase):
    def world(self,pak='maze_muncher',mix=None):
        world=World(Preferences(),24,solo=pak if mix is None else None,fixed_mix=mix)
        self.addCleanup(world.close)
        return world

    def modules(self):
        mix=json.loads((ROOT/'tests/cases/iron-maze-tail.json').read_text())['mix']
        world=self.world(mix=mix)
        nav=importlib.import_module(type(world.component('enemy')).__module__+'.navigation')
        geometry=importlib.import_module(type(world.component('weapon')).__module__+'.geometry')
        world.cover=[]
        return world,nav,geometry

    def test_recreated_live_shapes_share_one_graph_across_enemies(self):
        world,nav,g=self.modules()
        enemies=[Enemy(id=i,pos=Vec(500,200+i*10),radius=14) for i in range(8)]
        graphs={};routes=[nav.Route(graphs=graphs) for _ in enemies]
        def lines():return [g.LiveLine(Vec(220,80),Vec(320,210),world.component('weapon'),2)]
        world.set_geometry('tail',lines())
        with patch(nav.__name__+'._rectangular_graph',wraps=nav._rectangular_graph) as build:
            for route,body in zip(routes,enemies):route.direction(world,Vec(100,100),body)
            self.assertEqual(build.call_count,1)
            original=routes[0].nodes
            world.set_geometry('tail',lines())  # Same collision, fresh object identity.
            for route,body in zip(routes,enemies):route.direction(world,Vec(100,100),body)
            self.assertEqual(build.call_count,1)
            self.assertTrue(all(route.nodes is original for route in routes))
            changed=lines();changed[0].b.y+=32;changed[0].rect=g.bounds([changed[0].a,changed[0].b],2)
            world.set_geometry('tail',changed)
            for route,body in zip(routes,enemies):route.direction(world,Vec(100,100),body)
            self.assertEqual(build.call_count,2)

    def test_bounded_custom_shape_graph_matches_conservative_queries(self):
        world,nav,g=self.modules()
        shapes=[Cover(pygame.Rect(0,200,18,60),90,90),
                g.LiveLine(Vec(120.3,90),Vec(680,345.7),world.component('weapon'),2.5),
                g.CarvedArea([Vec(230,150),Vec(430,110),Vec(370,350),Vec(240,300)],(50,100,200),14)]
        world.cover=shapes
        for radius in (11,14,14.3,22):
            body=Enemy(pos=Vec(500,200),radius=radius)
            for shape in shapes:shape.__dict__.pop('navigation_key',None)
            fast=nav.Route();direction=fast.direction(world,Vec(100,100),body)
            for shape in shapes:shape.navigation_key=lambda:None
            reference=nav.Route();expected=reference.direction(world,Vec(100,100),body)
            self.assertEqual((fast.nodes,fast.links,direction),(reference.nodes,reference.links,expected))

    def test_tail_snapshots_track_collision_state_and_ignore_presentation_lifetime(self):
        world,nav,g=self.modules()
        region=g.CarvedArea([Vec(100,100),Vec(220,100),Vec(220,220)],(50,100,200),14)
        original=region.navigation_key();region.remaining-=1
        self.assertEqual(region.navigation_key(),original)
        region.points[1].x+=1
        self.assertNotEqual(region.navigation_key(),original)
        class Unknown(Cover):
            def overlaps_circle(self,position,radius):return False
        self.assertIsNone(Unknown(pygame.Rect(0,0,10,10),1,1).navigation_key())

    def test_dense_region_queries_and_boundary_anchors_match_full_edge_scans(self):
        world,nav,g=self.modules()
        network=importlib.import_module(type(world.component('weapon')).__module__+'.network')
        points=[Vec(400+math.cos(i*math.tau/80)*(130 if i%2 else 160),240+math.sin(i*math.tau/80)*(130 if i%2 else 160)) for i in range(80)]
        region=g.CarvedArea(points,(50,100,200),15)
        segments=list(zip(region.points,region.points[1:]+region.points[:1]))
        for radius in (0,11,14,15,15.3,22):
            for x in range(230,581,17):
                for y in range(70,411,19):
                    point=Vec(x,y)
                    distance=min(g.closest(point,a,b).distance_to(point) for a,b in segments)
                    expected=(distance+radius>region.inset if g.inside(point,points) else radius>distance+region.inset)
                    expected=expected and region.rect.inflate(radius*2,radius*2).collidepoint(point)
                    self.assertEqual(region.overlaps_circle(point,radius),bool(expected),(point,radius))
                    best=min((g.closest(point,a,b) for a,b in segments),key=lambda p:p.distance_squared_to(point))
                    expected_anchor=best if best.distance_to(point)<=6 else None
                    self.assertEqual(network.anchor(point,segments),expected_anchor)
        start,end=points[0],points[40]
        indexed=network.path(segments,start,end)
        with patch(network.__name__+'.candidate_pairs',side_effect=lambda edges:[range(index) for index in range(len(edges))]):
            self.assertEqual(network.path(segments,start,end),indexed)

    def test_all_maze_facing_poses_preserve_the_complete_measured_source_subject(self):
        world=self.world();pilot=world.component('pilot')
        source=pygame.image.load(ROOT/'assets/images/maze_muncher-facing-source.png')
        cells=source_cells(source.get_size(),4,4,[0,316,603,895,1246])
        for phase in range(4):
            world.time=(phase+.1)/8
            for facing in range(4):
                world.player.angle=facing*math.pi/2
                frame=pilot.sprite(world)
                rendered=frame.image.surface.subsurface(frame.rect)
                cell=source.subsurface(cells[phase*4+facing])
                boxes=[m.get_bounding_rects()[0] for m in pygame.mask.from_surface(cell,110).connected_components(80)]
                subject=cell.subsurface(boxes[0].unionall(boxes[1:]))
                self.assertEqual(pygame.mask.from_surface(subject,110).count(),pygame.mask.from_surface(rendered,110).count(),(phase,facing))
                self.assertGreater(rendered.get_bounding_rect(min_alpha=110).top,0)
                self.assertLess(rendered.get_bounding_rect(min_alpha=110).bottom,rendered.get_height())

    def test_nonteleport_enemies_do_not_schedule_attack_markers(self):
        for pak in get_catalog().complete_ids():
            if pak=='phase_garden':continue
            world=self.world(pak);world.phase='active'
            for _ in range(240):
                world.step(FIXED_DT,Controls())
                self.assertFalse([s for s in world.projectiles if type(s).__name__=='Warning' or type(s).__name__.endswith('Cue')],pak)

    def test_delayed_hazards_are_invisible_until_damage_activates(self):
        for pak in ('pulse_abbey','scrap_ballet','glasswake','bloom_siege','echo_vault','tidal_choir','sky_forge'):
            world=self.world(pak)
            module=importlib.import_module(type(world.component('enemy')).__module__+'.hazards')
            zone=module.EmberRing(Vec(300,200),10) if pak=='sky_forge' else module.Zone(Vec(300,200),30,.85,10)
            surface=pygame.Surface((960,480),pygame.SRCALPHA)
            zone.draw(None,surface,world)
            self.assertEqual(surface.get_bounding_rect().width,0,pak)
            zone.age=.9;zone.draw(None,surface,world)
            self.assertGreater(surface.get_bounding_rect().width,0,pak)

    def test_phase_warning_only_marks_the_teleport_destination(self):
        world=self.world('phase_garden');enemy=world.enemies[0]
        enemy.state='mark';enemy.destination=Vec(400,220);enemy.target=Vec(650,220)
        module=importlib.import_module(type(world.component('enemy')).__module__+'.telegraph')
        cue=module.RuneCue(enemy);surface=pygame.Surface((960,480),pygame.SRCALPHA)
        cue.draw(None,surface,world)
        self.assertGreater(surface.get_bounding_rect().width,0)
        self.assertEqual(surface.get_at((500,220)).a,0)
        surface.fill((0,0,0,0));enemy.state='exposed';cue.draw(None,surface,world)
        self.assertEqual(surface.get_bounding_rect().width,0)

    def test_weapon_readouts_leave_the_fixed_top_left_clear(self):
        from system_panic.graphics import Graphics
        pygame.init();pygame.display.set_mode((1,1))
        self.addCleanup(pygame.quit)
        graphics=Graphics()
        for pak in get_catalog().complete_ids():
            world=self.world(pak);world.player.pos=Vec(500,240)
            weapon=world.component('weapon')
            weapon.update(world,.1,Controls(fire=True))
            if hasattr(weapon,'charge'):weapon.charge=.9
            for obj in [*world.projectiles,*world.effects]:
                if type(obj).__name__ not in ('Readout','BiteReadout','PressureLine'):continue
                if type(obj).__name__ in ('BiteReadout','PressureLine'):obj.update(0)
                else:obj.update(world,0)
                surface=pygame.Surface((960,480),pygame.SRCALPHA)
                obj.draw(graphics,surface,world)
                self.assertEqual(surface.subsurface((0,0,220,80)).get_bounding_rect().width,0,pak)
