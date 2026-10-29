"""Initial-twelve quality contracts; all gameplay rules remain in their Paks."""
import hashlib
import importlib
import json
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
from system_panic.model import Controls,Cover,FIXED_DT,Vec
from system_panic.pak_assets import ImageAsset,SpriteFrame
from system_panic.paks import discover
from system_panic.preferences import Preferences
from system_panic.world import World

RENEWED=('signal_runner','void_drifter','iron_circuit','sky_forge','phase_garden','orbit_keeper',
         'neon_breach','maze_muncher','burrow_patrol','vector_coil','star_bastion','tide_hopper')

class RenewalTests(unittest.TestCase):
    def world(self,pak):
        world=World(Preferences(),24,solo=pak)
        self.addCleanup(world.close)
        world.cover=[]
        world.enemies.clear()
        world.player.pos=Vec(200,200)
        world.phase='active'
        return world

    def attack(self,world,seconds,fire):
        for _ in range(round(seconds/FIXED_DT)):
            world.time+=FIXED_DT
            world.component('weapon').update(world,FIXED_DT,Controls(fire=fire))
            world.update_projectiles(FIXED_DT)

    def test_signal_continuous_fire_overheats_and_release_restores_a_burst(self):
        world=self.world('signal_runner')
        weapon=world.component('weapon')
        with patch.object(weapon,'fire',wraps=weapon.fire) as fire:
            self.attack(world,3.,True)
            self.assertTrue(weapon.locked)
            self.assertLessEqual(fire.call_count,8)
            before=fire.call_count
            self.attack(world,1.,False)
            self.assertFalse(weapon.locked)
            self.assertEqual(weapon.heat,0)
            self.attack(world,.2,True)
            self.assertGreater(fire.call_count,before)

    def test_signal_leech_locks_a_lunge_and_recovers_without_attack_markers(self):
        world=self.world('signal_runner')
        part=world.component('enemy')
        enemy=world.spawn_enemy(Vec(300,200))
        enemy.timer=0
        part.advance_enemy(world,enemy,FIXED_DT)
        self.assertEqual(enemy.state,'windup')
        target=enemy.target.copy()
        before=world.player.health
        world.player.invulnerable=0
        part.on_contact(world,enemy,FIXED_DT)
        self.assertEqual(world.player.health,before)
        world.player.pos=Vec(200,400)
        part.advance_enemy(world,enemy,.43)
        self.assertEqual(enemy.target,target)
        self.assertEqual(enemy.state,'charge')
        self.assertLess(abs(enemy.vel.y),1)
        part.advance_enemy(world,enemy,.33)
        self.assertEqual(enemy.state,'recover')
        part.on_contact(world,enemy,FIXED_DT)
        self.assertEqual(world.player.health,before)
        world.projectiles.clear()
        part.advance_enemy(world,enemy,FIXED_DT)
        self.assertFalse(world.projectiles)

    def test_void_charge_needs_release_and_applies_recoil_without_creating_tap_shots(self):
        world=self.world('void_drifter')
        weapon=world.component('weapon')
        self.attack(world,.1,True)
        self.attack(world,.1,False)
        self.assertFalse(any(type(s).__name__=='Lance' for s in world.projectiles))
        self.attack(world,1.15,True)
        self.assertFalse(any(type(s).__name__=='Lance' for s in world.projectiles))
        world.player.angle=0
        self.attack(world,FIXED_DT,False)
        shots=[s for s in world.projectiles if type(s).__name__=='Lance']
        self.assertEqual(len(shots),1)
        self.assertGreater(shots[0]._damage,70)
        self.assertLess(world.player.vel.x,-100)

    def test_void_charge_grows_damage_and_a_real_per_target_piercing_budget(self):
        hits=[]
        damages=[]
        for seconds in (.18,1.15):
            world=self.world('void_drifter')
            enemies=[world.spawn_enemy(Vec(x,200)) for x in (300,350,400)]
            for enemy in enemies:enemy.health=enemy.max_health=1000
            self.attack(world,seconds,True)
            self.attack(world,.6,False)
            hits.append(sum(e.health<1000 for e in enemies))
            damages.append(1000-enemies[0].health)
        self.assertEqual(hits,[1,3])
        self.assertGreater(damages[1],damages[0]*3)

    def test_iron_speed_strengthens_plasma_and_a_bank_adds_power(self):
        world=self.world('iron_circuit')
        weapon=world.component('weapon')
        module=importlib.import_module(type(weapon).__module__+'.projectile')
        world.player.vel=Vec(70,0)
        slow=module.Ricochet(world,weapon,Vec(1,0))
        world.player.vel=Vec(330,0)
        fast=module.Ricochet(world,weapon,Vec(1,0))
        self.assertGreater(fast._damage,slow._damage*1.5)
        world.player.pos=Vec(935,100)
        bank=module.Ricochet(world,weapon,Vec(1,0))
        before=bank._damage
        bank.update(world,.1)
        self.assertLess(bank.vel.x,0)
        self.assertGreater(bank._damage,before*1.5)

    def test_iron_turret_commits_to_a_tell_and_exposes_armor_after_firing(self):
        world=self.world('iron_circuit')
        part=world.component('enemy')
        enemy=world.spawn_enemy(Vec(400,200))
        enemy.health=enemy.max_health=1000
        enemy.timer=0
        part.advance_enemy(world,enemy,FIXED_DT)
        self.assertEqual(enemy.state,'windup')
        target=enemy.target.copy()
        world.player.pos=Vec(200,400)
        part.advance_enemy(world,enemy,.6)
        self.assertEqual(enemy.target,target)
        self.assertEqual(enemy.state,'recover')
        shots=[s for s in world.projectiles if type(s).__name__=='HostileShot']
        self.assertTrue(shots)
        self.assertLess(abs(shots[0].vel.y),1)
        exposed=world.hit_enemy(enemy,10)
        enemy.state='idle'
        armored=world.hit_enemy(enemy,10)
        self.assertGreater(exposed,armored*2)

    def test_phase_lightning_has_finite_reach_links_and_respects_deliberate_aim(self):
        world=self.world('phase_garden')
        weapon=world.component('weapon')
        far=world.spawn_enemy(Vec(900,200))
        far.health=far.max_health=1000
        weapon.fire(world,Vec(1,0))
        self.assertEqual(far.health,1000)
        world.enemies.clear()
        first=world.spawn_enemy(Vec(300,200))
        second=world.spawn_enemy(Vec(470,200))
        for enemy in world.enemies:enemy.health=enemy.max_health=1000
        weapon.fire(world,Vec(1,0))
        self.assertLess(first.health,1000)
        self.assertEqual(second.health,1000)
        world.powerups_collected=12
        weapon.fire(world,Vec(1,0))
        self.assertLess(second.health,1000)
        world.component('pilot').aim_direction=lambda w:Vec(-1,0)
        before=[e.health for e in world.enemies]
        weapon.fire(world,weapon.aim(world))
        self.assertEqual(before,[e.health for e in world.enemies])

    def test_phase_warp_is_marked_before_relocation_and_exposes_the_phantom(self):
        world=self.world('phase_garden')
        part=world.component('enemy')
        enemy=world.spawn_enemy(Vec(500,200))
        enemy.health=enemy.max_health=1000
        enemy.timer=0
        start=enemy.pos.copy()
        part.advance_enemy(world,enemy,FIXED_DT)
        self.assertEqual(enemy.state,'mark')
        self.assertEqual(enemy.pos,start)
        target=enemy.target.copy()
        world.player.pos=Vec(200,400)
        part.advance_enemy(world,enemy,.61)
        self.assertEqual(enemy.state,'exposed')
        self.assertNotEqual(enemy.pos,start)
        shot=next(s for s in world.projectiles if s.is_threat_to(world,world.player))
        self.assertLess(abs(shot.vel.normalize().cross((target-enemy.pos).normalize())),.001)
        exposed=world.hit_enemy(enemy,10)
        enemy.state='drift'
        shielded=world.hit_enemy(enemy,10)
        self.assertGreater(exposed,shielded*2)

    def test_orbit_blade_pool_and_deliberate_catch_reward(self):
        world=self.world('orbit_keeper')
        weapon=world.component('weapon')
        self.attack(world,.51,True)
        self.assertEqual(len(weapon._active),2)
        weapon.fire(world,Vec(1,0))
        self.assertEqual(len(weapon._active),2)
        weapon.caught(world)
        self.assertEqual(weapon.next_boost,1)
        self.attack(world,FIXED_DT,False)
        weapon.caught(world)
        self.assertEqual(weapon.next_boost,1.8)
        world.projectiles.clear()
        weapon._active.clear()
        weapon.fire(world,Vec(1,0))
        self.assertAlmostEqual(weapon._active[0]._damage,28*1.8)
        self.assertEqual(weapon.next_boost,1)
        weapon.on_level_start(world)
        self.attack(world,.1,True)
        self.attack(world,FIXED_DT,False)
        weapon.caught(world)
        self.assertEqual(weapon.next_boost,1)

    def test_orbit_blade_can_cut_once_on_each_leg_and_return_through_cover(self):
        world=self.world('orbit_keeper')
        weapon=world.component('weapon')
        enemy=world.spawn_enemy(Vec(250,200))
        enemy.health=enemy.max_health=1000
        module=importlib.import_module(type(weapon).__module__+'.projectile')
        shot=module.Glaive(world,weapon,Vec(1,0))
        shot.pos=enemy.pos.copy()
        shot.update(world,0)
        health=enemy.health
        shot.update(world,0)
        self.assertEqual(enemy.health,health)
        shot._age=shot._outbound+.01
        world.cover=[Cover(pygame.Rect(240,180,20,40),100,100)]
        shot.update(world,0)
        self.assertTrue(shot.alive)
        self.assertLess(enemy.health,health)

    def test_orbit_sentinel_locks_its_tell_and_opens_after_firing(self):
        world=self.world('orbit_keeper')
        part=world.component('enemy')
        enemy=world.spawn_enemy(Vec(400,200))
        enemy.health=enemy.max_health=1000
        enemy.timer=0
        part.advance_enemy(world,enemy,FIXED_DT)
        self.assertEqual(enemy.state,'aim')
        target=enemy.target.copy()
        world.player.pos=Vec(100,400)
        part.advance_enemy(world,enemy,.51)
        self.assertEqual(enemy.target,target)
        self.assertEqual(enemy.state,'open')
        shot=next(s for s in world.projectiles if s.is_threat_to(world,world.player))
        self.assertLess(abs(shot.vel.normalize().cross((target-enemy.pos).normalize())),.001)
        exposed=world.hit_enemy(enemy,10)
        enemy.state='guard'
        shielded=world.hit_enemy(enemy,10)
        self.assertGreater(exposed,shielded*2)

    def test_neon_misses_drain_energy_and_a_moving_paddle_builds_an_angled_return(self):
        world=self.world('neon_breach')
        weapon=world.component('weapon')
        module=importlib.import_module(type(weapon).__module__+'.projectile')
        world.player.pos=Vec(480,468)
        world.player.edge=2
        world.player.angle=-3.141592653589793/2
        ball=module.PlasmaBall(world,weapon,Vec(0,-1))
        ball.pos,ball.vel=Vec(100,470),Vec(0,420)
        ball.update(world,.02)
        self.assertAlmostEqual(ball.energy,.85)
        world.player.vel=Vec(250,0)
        ball.pos,ball.vel=Vec(480,442),Vec(0,420)
        ball.update(world,.01)
        self.assertGreater(ball.energy,1.2)
        self.assertLess(ball.vel.y,0)
        self.assertGreater(abs(ball.vel.x),30)
        self.assertEqual(weapon.returns,1)
        self.assertFalse(ball.guided)

    def test_maze_snap_cannot_put_the_pilot_inside_an_unaligned_wall(self):
        world=self.world('maze_muncher')
        world.cover=[Cover(pygame.Rect(402,306,22,69),36,36)]
        world.player.pos=Vec(435,351)
        pilot=world.component('pilot')
        pilot._direction=Vec(1,0)
        pilot.update(world,FIXED_DT,Controls(y=1))
        self.assertGreaterEqual(world.player.pos.x,435)
        self.assertGreater(world.player.pos.y,351)

    def test_maze_demo_uses_reachable_grid_waypoints_after_a_target_moves_away(self):
        world=self.world('maze_muncher')
        pilot=world.component('pilot')
        enemy=world.spawn_enemy(Vec(496,341))
        world.player.pos=Vec(490,352)
        pilot.demo_controls(world)
        enemy.pos=Vec(880,280)
        start=world.player.pos.copy()
        for _ in range(240):
            world.time+=FIXED_DT
            control=pilot.demo_controls(world)
            pilot.update(world,FIXED_DT,control)
        self.assertGreater(world.player.pos.distance_to(start),200)

    def test_vector_demo_finishes_an_entry_waypoint_with_digital_controls(self):
        world=self.world('vector_coil')
        pilot=world.component('pilot')
        world.player.pos=Vec(410,218)
        start=world.player.pos.copy()
        for _ in range(360):
            world.time+=FIXED_DT
            control=pilot.demo_controls(world)
            self.assertIn(control.x,(-1,0,1))
            self.assertIn(control.y,(-1,0,1))
            pilot.update(world,FIXED_DT,control)
        self.assertGreater(world.player.pos.distance_to(start),250)

    def test_maze_backbite_is_stronger_and_contact_separation_is_safe(self):
        damages=[]
        for velocity in (Vec(-50,0),Vec(50,0)):
            world=self.world('maze_muncher')
            world.player.angle=0
            enemy=world.spawn_enemy(Vec(226,200))
            enemy.health=enemy.max_health=1000
            enemy.vel=velocity
            world.component('weapon').update(world,FIXED_DT,Controls(fire=True))
            damages.append(1000-enemy.health)
            self.assertGreater(world.player.invulnerable,0)
            self.assertGreater(enemy.stunned,0)
            world.player.invulnerable=0
            before=world.player.health
            world.component('enemy').on_contact(world,enemy,FIXED_DT)
            self.assertEqual(world.player.health,before)
        self.assertGreater(damages[1],damages[0]*1.5)

    def test_maze_crabs_share_only_rectangle_graphs_and_keep_routes_independent(self):
        world=self.world('maze_muncher')
        world.cover=[Cover(pygame.Rect(350,100,24,220),36,36)]
        part=world.component('enemy')
        module=importlib.import_module(type(part).__module__+'.navigation')
        enemies=[world.spawn_enemy(Vec(450,y)) for y in (180,260)]
        routes=[module.Route(False,part._graphs) for _ in enemies]
        for route,enemy in zip(routes,enemies):
            actual=route.direction(world,world.player.pos,enemy)
            fresh=module.Route(False).direction(world,world.player.pos,enemy)
            self.assertEqual(actual,fresh)
        self.assertIs(routes[0].nodes,routes[1].nodes)
        self.assertIsNot(routes[0].waypoint,routes[1].waypoint)
        self.assertEqual(len(part._graphs),1)
        class Selective(Cover):
            def blocks_body(self,body):return body is enemies[0]
        world.cover=[Selective(pygame.Rect(350,100,24,220),36,36)]
        one=module.Route(False,part._graphs)
        two=module.Route(False,part._graphs)
        one.direction(world,world.player.pos,enemies[0])
        two.direction(world,world.player.pos,enemies[1])
        self.assertIsNot(one.nodes,two.nodes)
        part.on_level_start(world)
        self.assertFalse(part._graphs)

    def test_burrow_pop_has_recovery_and_cannot_carry_pressure_to_a_new_target(self):
        world=self.world('burrow_patrol')
        weapon=world.component('weapon')
        enemy=world.spawn_enemy(Vec(300,200))
        enemy.health=enemy.max_health=80
        self.attack(world,1.2,True)
        self.assertEqual(enemy.health,0)
        self.assertGreater(weapon.recovery,0)
        other=world.spawn_enemy(Vec(310,200))
        before=other.health
        self.attack(world,.1,True)
        self.assertEqual(other.health,before)
        self.attack(world,.3,False)
        other.pos=Vec(900,200)
        self.attack(world,.3,True)
        self.assertIsNone(weapon._target)
        self.assertEqual(weapon._pressure,0)

    def test_burrow_emergence_is_safe_and_locks_the_rush(self):
        world=self.world('burrow_patrol')
        enemy=world.spawn_enemy(Vec(400,200))
        part=world.component('enemy')
        enemy.timer=0
        part.advance_enemy(world,enemy,FIXED_DT)
        self.assertEqual(enemy.state,'burrow')
        part.advance_enemy(world,enemy,.91)
        self.assertEqual(enemy.state,'rush')
        target=enemy.target.copy()
        before=world.player.health
        world.player.invulnerable=0
        part.on_contact(world,enemy,FIXED_DT)
        self.assertLess(world.player.health,before)
        world.player.pos=Vec(100,400)
        part.advance_enemy(world,enemy,.1)
        self.assertEqual(enemy.state,'rush')
        self.assertEqual(enemy.target,target)
        self.assertLess(abs(enemy.vel.y),1)

    def test_vector_empty_territory_expires_without_applying_capture_damage(self):
        world=self.world('vector_coil')
        weapon=world.component('weapon')
        enemy=world.spawn_enemy(Vec(500,300))
        health=enemy.health
        for position in ((200,200),(320,200),(320,320),(200,320),(200,190)):
            world.player.pos=Vec(position)
            weapon.update(world,FIXED_DT,Controls(fire=True))
        self.assertEqual(len(weapon._areas),1)
        weapon.update(world,22.1,Controls())
        self.assertFalse(weapon._areas)
        self.assertEqual(enemy.health,health)
        self.assertFalse(world.geometry)

    def test_star_battery_empty_lock_and_early_release_reload(self):
        world=self.world('star_bastion')
        weapon=world.component('weapon')
        self.attack(world,1.0,True)
        self.assertEqual(weapon.cells,0)
        self.assertGreater(weapon.reloading,1.2)
        before=len([s for s in world.projectiles if type(s).__name__=='SalvoBolt'])
        self.attack(world,.2,True)
        self.assertEqual(len([s for s in world.projectiles if type(s).__name__=='SalvoBolt']),before)
        weapon.on_level_start(world)
        self.attack(world,FIXED_DT,True)
        self.assertEqual(weapon.cells,3)
        self.attack(world,.5,False)
        self.assertEqual(weapon.cells,4)

    def test_star_fires_without_a_tell_and_dives_with_exposed_armor(self):
        world=self.world('star_bastion')
        world.wave=5
        part=world.component('enemy')
        enemy=world.spawn_enemy(Vec(400,200))
        enemy.health=enemy.max_health=1000
        enemy.timer=0
        part.advance_enemy(world,enemy,FIXED_DT)
        self.assertEqual(enemy.state,'dive')
        self.assertEqual(sum(type(s).__name__=='HostileShot' for s in world.projectiles),3)
        self.assertFalse(any(type(s).__name__=='DiveCue' for s in world.projectiles))
        target=enemy.target.copy()
        world.player.pos=Vec(100,400)
        part.advance_enemy(world,enemy,.66)
        self.assertEqual(enemy.state,'dive')
        self.assertEqual(enemy.target,target)
        exposed=world.hit_enemy(enemy,10)
        enemy.state='formation'
        shielded=world.hit_enemy(enemy,10)
        self.assertGreater(exposed,shielded*2)

    def test_tide_tow_respects_body_geometry_and_release_flings_into_another_enemy(self):
        world=self.world('tide_hopper')
        weapon=world.component('weapon')
        module=importlib.import_module(type(weapon).__module__+'.projectile')
        target=world.spawn_enemy(Vec(400,200))
        target.health=target.max_health=200
        hook=module.Harpoon(world,weapon,Vec(1,0))
        hook.target=target
        weapon.fire_held=True
        world.cover=[Cover(pygame.Rect(290,150,20,100),1000,1000)]
        for _ in range(45):hook.update(world,FIXED_DT)
        self.assertGreaterEqual(target.pos.x,324)
        world.cover=[]
        target.pos=Vec(350,200)
        other=world.spawn_enemy(Vec(420,200))
        other.health=other.max_health=200
        hook.target,hook.blocked=target,0
        weapon.fire_held=False
        hook.update(world,FIXED_DT)
        self.assertTrue(hook.flung)
        for _ in range(20):
            if hook.alive:hook.update(world,FIXED_DT)
        self.assertFalse(hook.alive)
        self.assertLess(target.health,200)
        self.assertLess(other.health,200)

    def test_sky_stab_and_throw_have_distinct_damage_and_throw_requires_recovery(self):
        world=self.world('sky_forge')
        weapon=world.component('weapon')
        module=importlib.import_module(type(weapon).__module__+'.projectile')
        enemy=world.spawn_enemy(Vec(250,200))
        enemy.health=enemy.max_health=1000
        stab=module.Swing(world,weapon,Vec(1,0))
        stab.update(world,.21)
        self.assertEqual(enemy.health,1000-stab._damage)
        stab.update(world,.21)
        self.assertEqual(enemy.health,1000-stab._damage)
        weapon.fire(world,Vec(1,0),1.3)
        sword=weapon._sword
        self.assertGreater(sword._damage,stab._damage*4)
        sword.update(world,.04)
        self.assertEqual(sword.state,'resting')
        self.assertEqual(enemy.health,1000-stab._damage-sword._damage)
        before=len(world.projectiles)
        weapon.fire(world,Vec(1,0))
        self.assertEqual(len(world.projectiles),before)
        sword.pos=world.player.pos.copy();sword.pickup_lock=0
        sword.update(world,0)
        self.assertIsNone(weapon._sword)
        self.assertFalse(sword.alive)

    def test_sky_crawlers_fall_to_decks_and_lock_their_leap(self):
        world=self.world('sky_forge')
        part=world.component('enemy')
        enemy=world.spawn_enemy(Vec(300,160))
        enemy.timer=100
        world.player.pos=Vec(300,200)
        for _ in range(180):part.advance_enemy(world,enemy,FIXED_DT)
        self.assertTrue(enemy.grounded)
        self.assertAlmostEqual(enemy.pos.y,480-enemy.radius)
        world.player.pos=Vec(500,250)
        enemy.timer=0
        part.advance_enemy(world,enemy,FIXED_DT)
        self.assertEqual(enemy.state,'windup')
        launch=enemy.launch.copy()
        world.player.pos=Vec(100,400)
        for _ in range(50):part.advance_enemy(world,enemy,FIXED_DT)
        self.assertEqual(enemy.launch,launch)
        self.assertEqual(enemy.state,'leap')
        self.assertGreater(enemy.vel.x,0)
        self.assertLess(enemy.vel.y,0)
        for _ in range(150):part.advance_enemy(world,enemy,FIXED_DT)
        self.assertTrue(enemy.grounded)
        self.assertEqual(enemy.state,'recover')

    def test_sky_rooftop_heat_keeps_its_delay_and_hits_once(self):
        world=self.world('sky_forge')
        part=world.component('enemy')
        enemy=world.spawn_enemy(Vec(300,456))
        enemy.grounded,enemy.timer=True,0
        world.player.pos,world.player.invulnerable=Vec(300,200),0
        part.advance_enemy(world,enemy,FIXED_DT)
        zone=next(s for s in world.projectiles if type(s).__name__=='EmberRing')
        self.assertTrue(zone.is_threat_to(world,world.player))
        before=world.player.health
        zone.update(world,.8)
        self.assertEqual(world.player.health,before)
        zone.update(world,.1)
        self.assertLess(world.player.health,before)
        after=world.player.health
        world.player.invulnerable=0
        zone.update(world,.1)
        self.assertEqual(world.player.health,after)

    def test_sky_enemy_art_feet_fit_the_flat_foot_collision_radius(self):
        from system_panic.graphics import Graphics
        world=self.world('sky_forge')
        enemy=world.spawn_enemy(Vec(300,200))
        enemy.state='recover'
        pygame.init()
        pygame.display.set_mode((1,1))
        try:
            image=Graphics().component_sprite(world,'enemy',enemy,int(enemy.radius*3.4),rotate=False)
            bounds=image.get_bounding_rect(min_alpha=110)
            self.assertLessEqual(bounds.bottom-image.get_height()/2,enemy.radius+1)
        finally:pygame.quit()

    def test_sky_crawler_finishes_a_descent_instead_of_oscillating_at_a_deck_lip(self):
        world=self.world('sky_forge')
        world.cover=[Cover(pygame.Rect(200,200,140,16),36,36)]
        world.player.pos=Vec(260,448)
        enemy=world.spawn_enemy(Vec(205,186))
        enemy.grounded,enemy.timer=True,100
        part=world.component('enemy')
        for _ in range(300):part.advance_enemy(world,enemy,FIXED_DT)
        self.assertGreater(enemy.pos.y,300)

    def test_sky_demo_finishes_its_drop_using_only_normal_digital_input(self):
        world=self.world('sky_forge')
        world.cover=[Cover(pygame.Rect(200,200,140,16),36,36)]
        world.player.pos=Vec(205,178)
        enemy=world.spawn_enemy(Vec(260,448))
        enemy.timer=100
        pilot=world.component('pilot')
        for _ in range(300):
            control=pilot.demo_controls(world)
            self.assertIn(control.x,(-1,0,1))
            pilot.update(world,FIXED_DT,control)
        self.assertGreater(world.player.pos.y,300)

    def test_renewed_scenery_animation_and_owned_terrain_draw_without_simulation_mutation(self):
        from system_panic.graphics import Graphics
        pygame.init()
        pygame.display.set_mode((1,1))
        graphics=Graphics()
        surface=pygame.Surface((960,480))
        try:
            for pak in RENEWED:
                w=World(Preferences(),24,solo=pak)
                try:
                    w.time=1.25
                    before=(w.time,w.rng.getstate(),w.player.pos.copy(),[(e.pos.copy(),e.health) for e in w.enemies])
                    graphics.draw_world(surface,w)
                    graphics.draw_world(surface,w)
                    self.assertEqual(before,(w.time,w.rng.getstate(),w.player.pos,[(e.pos,e.health) for e in w.enemies]),pak)
                finally:w.close()
        finally:pygame.quit()

    def test_all_48_roles_have_four_visible_distinct_frames_and_read_only_selection(self):
        for pak in RENEWED:
            w=World(Preferences(),24,solo=pak)
            try:
                before=(w.time,w.rng.getstate(),w.player.pos.copy())
                for role in ('pilot','enemy','weapon','obstacles'):
                    part=w.component(role)
                    handle=part.sprite(w)
                    self.assertIsInstance(handle,(SpriteFrame,ImageAsset),(pak,role))
                    art=handle.image if isinstance(handle,SpriteFrame) else handle
                    metadata=json.loads((ROOT/'paks'/pak/'pak.json').read_text())
                    columns,rows=metadata['authoring'].get('component_grids',{}).get(role,[4,1])
                    if columns*rows>1:self.assertEqual(art.surface.get_width()//columns,art.surface.get_height()//rows,(pak,role))
                    hashes=set()
                    for frame in range(1 if columns*rows==1 else 4):
                        index=frame*columns if rows==4 else frame
                        pixels=art.surface.subsurface(art.frame(index,columns=columns,rows=rows).rect)
                        self.assertGreater(pygame.mask.from_surface(pixels).count(),100,(pak,role,frame))
                        hashes.add(hashlib.sha256(pygame.image.tobytes(pixels,'RGBA')).hexdigest())
                    self.assertEqual(len(hashes),1 if columns*rows==1 else 4,(pak,role))
                    self.assertIsInstance(part.preview(),(SpriteFrame,ImageAsset))
                self.assertEqual(before,(w.time,w.rng.getstate(),w.player.pos))
                pickup=w.component('weapon').create_powerup(w,w.player.pos)
                self.assertIsInstance(pickup.art,ImageAsset,pak)
                self.assertEqual(pickup.art.path.parent,ROOT/'paks'/pak/'weapon')
            finally:w.close()

    def test_each_renewed_pak_loads_and_updates_with_all_other_paks_absent(self):
        (ROOT/'output').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'output') as directory:
            for pak in RENEWED:
                folder=Path(directory)/pak
                shutil.copytree(ROOT/'paks'/pak,folder/pak,ignore=shutil.ignore_patterns('__pycache__'))
                catalog=discover([folder])
                self.assertFalse(catalog.issues,(pak,catalog.issues))
                self.assertEqual(catalog.complete_ids(),(pak,))
                w=World(Preferences(),24,solo=pak,catalog=catalog)
                try:
                    w.phase='active'
                    for frame in range(90):w.step(FIXED_DT,Controls(1,0,frame%60<45,frame==0))
                finally:w.close()

    def test_each_renewed_pak_also_works_as_six_complementary_partial_folders(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'output') as directory:
            for pak in RENEWED:
                source=ROOT/'paks'/pak
                root=Path(directory)/pak
                for role in ('pilot','enemy','weapon','music','background','obstacles'):
                    folder=root/(pak+'_'+role)
                    shutil.copytree(source/role,folder/role,ignore=shutil.ignore_patterns('__pycache__'))
                    data=json.loads((source/'pak.json').read_text())
                    data.update(id=folder.name,components=[role])
                    (folder/'pak.json').write_text(json.dumps(data))
                catalog=discover([root])
                self.assertFalse(catalog.issues,(pak,catalog.issues))
                self.assertFalse(catalog.complete_ids())
                w=World(Preferences(shuffle_channels=[]),24,catalog=catalog)
                try:
                    w.phase='active'
                    for frame in range(120):w.step(FIXED_DT,Controls(1,0,frame<85,frame==0))
                finally:w.close()

    def test_both_legacy_exporters_preserve_animated_sources_and_derivative_records(self):
        from tools.assetforge import export_paks,export_expansion
        with tempfile.TemporaryDirectory(dir=ROOT/'output') as directory:
            root=Path(directory)
            (root/'assets/images').mkdir(parents=True)
            pygame.image.save(pygame.Surface((8,8),pygame.SRCALPHA),root/'assets/images/sprites-source.png')
            folder=root/'paks/animated'
            (folder/'pilot').mkdir(parents=True)
            (folder/'pak.json').write_text(json.dumps(dict(id='animated',authoring=dict(atlas_column=0,animation_grid=[4,4],sheet_source='animated-source.png'))))
            art=folder/'pilot/pilot_sheet.png'
            art.write_bytes(b'preserve original animation row bytes')
            ledger=root/'assets/pak-exports.json'
            entries=[dict(file='paks/animated/pilot/pilot_sheet.png',operation='measured row extraction')]
            ledger.write_text(json.dumps(entries))
            for exporter in (export_paks,export_expansion):
                with patch.object(exporter,'ROOT',root):exporter.main()
                self.assertEqual(art.read_bytes(),b'preserve original animation row bytes')
                self.assertEqual(json.loads(ledger.read_text()),entries)

    def test_unchanged_audio_export_never_reopens_a_streamed_destination_for_writing(self):
        from tools.assetforge import export_renewal
        with tempfile.TemporaryDirectory(dir=ROOT/'output') as directory:
            root=Path(directory)
            for suffix,relative in (('','music/music.ogg'),('_shot','weapon/shot.ogg'),('_special','pilot/special.ogg')):
                source=root/f'assets/audio/production/probe{suffix}.ogg'
                target=root/f'paks/probe/{relative}'
                source.parent.mkdir(parents=True,exist_ok=True)
                target.parent.mkdir(parents=True,exist_ok=True)
                source.write_bytes(b'identical prepared audio')
                target.write_bytes(source.read_bytes())
            with patch.object(export_renewal,'ROOT',root),patch.object(export_renewal.shutil,'copyfile',side_effect=AssertionError('would reopen locked audio')) as copy:
                records=export_renewal.copy_audio([dict(id='probe')])
            copy.assert_not_called()
            self.assertEqual(len(records),3)

if __name__=='__main__':unittest.main()
