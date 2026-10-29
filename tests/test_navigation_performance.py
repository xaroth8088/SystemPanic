"""Moving rectangular terrain must not cause an enemy-count grid rebuild storm."""
import importlib
import os
from pathlib import Path
import sys
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pygame
from system_panic.model import Cover,Enemy,Vec
from system_panic.preferences import Preferences
from system_panic.world import World

class NavigationPerformanceTests(unittest.TestCase):
    def world(self):
        w=World(Preferences(),24,solo='maze_muncher');self.addCleanup(w.close);w.cover=[];w.enemies.clear()
        part=w.component('enemy');module=importlib.import_module(type(part).__module__+'.navigation')
        return w,part,module
    def test_rectangular_subclasses_share_one_snapshot_across_enemies(self):
        w,part,m=self.world()
        class Mirror(Cover):
            def blocks_body(self,body):return True
        wall=Mirror(pygame.Rect(230,70,14,75),90,90);w.cover=[wall]
        enemies=[w.spawn_enemy(Vec(500,200+i*20)) for i in range(8)]
        routes=[m.Route(True,part._graphs) for _ in enemies]
        for route,enemy in zip(routes,enemies):route.direction(w,w.player.pos,enemy)
        self.assertTrue(all(r.nodes is routes[0].nodes for r in routes))
        self.assertEqual(len(part._graphs),1)
        old=routes[0].nodes;wall.rect.x+=1
        for route,enemy in zip(routes,enemies):route.direction(w,w.player.pos,enemy)
        self.assertIsNot(routes[0].nodes,old)
        self.assertTrue(all(r.nodes is routes[0].nodes for r in routes))
    def test_body_specific_rectangular_filters_never_share_incompatible_graphs(self):
        w,part,m=self.world();a=w.spawn_enemy(Vec(500,200));b=w.spawn_enemy(Vec(500,260))
        class Selective(Cover):
            def blocks_body(self,body):return body is a
        w.cover=[Selective(pygame.Rect(300,100,80,240),90,90)]
        one,two=m.Route(True,part._graphs),m.Route(True,part._graphs)
        one.direction(w,w.player.pos,a);two.direction(w,w.player.pos,b)
        self.assertIsNot(one.nodes,two.nodes);self.assertLess(len(one.nodes),len(two.nodes))
        self.assertEqual(one.direction(w,w.player.pos,a),m.Route().direction(w,w.player.pos,a))
    def test_custom_overlap_queries_keep_their_actual_shape_and_per_body_graphs(self):
        w,part,m=self.world();enemies=[w.spawn_enemy(Vec(500,y)) for y in (200,260)]
        class Hollow(Cover):
            def overlaps_circle(self,pos,radius):return False
        w.cover=[Hollow(pygame.Rect(200,100,400,280),90,90)]
        routes=[m.Route(True,part._graphs) for _ in enemies]
        for r,e in zip(routes,enemies):r.direction(w,w.player.pos,e)
        self.assertEqual(len(routes[0].nodes),450);self.assertIsNot(routes[0].nodes,routes[1].nodes)
        self.assertFalse(part._graphs)
    def test_instance_overlap_override_is_not_mistaken_for_a_rectangle(self):
        w,part,m=self.world();wall=Cover(pygame.Rect(200,100,400,280),90,90)
        wall.overlaps_circle=lambda p,r:False;w.cover=[wall]
        route=m.Route(True,part._graphs);route.direction(w,w.player.pos)
        self.assertEqual(len(route.nodes),450);self.assertFalse(part._graphs)
    def test_moving_graph_cache_is_bounded_and_surviving_snapshots_stay_immutable(self):
        w,part,m=self.world();wall=Cover(pygame.Rect(230,70,14,75),90,90);w.cover=[wall]
        route=m.Route(True,part._graphs);route.direction(w,w.player.pos)
        original=route.nodes;copy={node:point.copy() for node,point in original.items()}
        for _ in range(32):
            wall.rect.x+=1;route.direction(w,w.player.pos)
            self.assertLessEqual(len(part._graphs),m.Route.MAX_GRAPHS)
        self.assertEqual(original,copy)
        part.on_level_start(w);self.assertFalse(part._graphs)
    def test_nonblocking_motion_does_not_invalidate_topology_but_filter_changes_do(self):
        w,part,m=self.world()
        class Gate(Cover):
            open=True
            def blocks_body(self,body):return not self.open
        wall=Gate(pygame.Rect(230,70,64,200),90,90);w.cover=[wall]
        route=m.Route(True,part._graphs);route.direction(w,w.player.pos);nodes=route.nodes
        wall.rect.x+=20;route.direction(w,w.player.pos);self.assertIs(route.nodes,nodes)
        wall.open=False;route.direction(w,w.player.pos);self.assertIsNot(route.nodes,nodes)
        self.assertLess(len(route.nodes),len(nodes))
    def test_broadphase_keeps_exact_fractional_radius_contact_results(self):
        w,part,m=self.world();w.cover=[Cover(pygame.Rect(225,65,17,83),90,90)]
        body=Enemy(pos=Vec(500,200),radius=14.3);route=m.Route();route.direction(w,w.player.pos,body)
        for y in (48,50.7,51,64.999,65,148,162.3,162.3001):
            for x in (209.7,210,225,241.9,242,256.3,256.3001):
                a=Vec(x,y);expected=not w.cover[0].overlaps_circle(a,body.radius+1)
                self.assertEqual(route.clear(w,a,a),expected,(x,y))
    def test_indexed_rectangle_graph_matches_custom_query_fallback_including_wrap(self):
        w,part,m=self.world()
        class Reference(Cover):
            def overlaps_circle(self,position,radius):return super().overlaps_circle(position,radius)
        for radius in (11,14,14.3,22):
            for offset in (0,1,17):
                rectangles=[pygame.Rect(230+offset,70,14,75),pygame.Rect(0,200+offset,18,80),pygame.Rect(940,300-offset,20,65)]
                body=Enemy(pos=Vec(500,240),radius=radius)
                w.cover=[Cover(r.copy(),90,90) for r in rectangles]
                fast=m.Route();direction=fast.direction(w,Vec(100,100),body)
                w.cover=[Reference(r.copy(),90,90) for r in rectangles]
                reference=m.Route();expected=reference.direction(w,Vec(100,100),body)
                self.assertEqual(fast.nodes,reference.nodes,(radius,offset))
                self.assertEqual(fast.links,reference.links,(radius,offset))
                self.assertEqual(direction,expected,(radius,offset))

if __name__=='__main__':unittest.main()
