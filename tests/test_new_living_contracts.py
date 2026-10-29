"""Cross-Pak contracts for the six independently installable Living Paks."""
import ast
import os
from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from system_panic.model import Controls, Vec, FIXED_DT
from system_panic.paks import get_catalog, discover, CHANNELS
from system_panic.preferences import Preferences
from system_panic.world import World

NEW=('canopy_capers','rime_rink','storm_loom','kiln_derby','paper_pilgrimage','ferric_ferry')


class LivingContractTests(unittest.TestCase):
    def test_every_new_complete_pak_and_its_six_partial_roles_install_without_other_paks(self):
        temporary_root=ROOT/'output/test-temp'
        temporary_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as temporary:
            for pak in NEW:
                alone=Path(temporary)/('alone-'+pak)
                shutil.copytree(ROOT/'paks'/pak,alone/pak,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
                catalog=discover([alone])
                self.assertEqual(catalog.issues,())
                self.assertEqual(catalog.complete_ids(),(pak,))
                w=World(Preferences(),24,solo=pak,catalog=catalog)
                try:
                    w.phase='active'
                    for step in range(120):w.step(FIXED_DT,Controls(1,-1,step%60<40,step<10))
                finally:w.close()
                partials=Path(temporary)/('partials-'+pak)
                for role in CHANNELS:
                    folder=partials/(pak+'_'+role)
                    shutil.copytree(ROOT/'paks'/pak/role,folder/role,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
                    metadata=json.loads((ROOT/'paks'/pak/'pak.json').read_text())
                    metadata.update(id=pak+'_'+role,components=[role])
                    (folder/'pak.json').write_text(json.dumps(metadata))
                catalog=discover([partials])
                self.assertEqual(catalog.issues,())
                self.assertFalse(catalog.complete_ids())
                w=World(Preferences(),24,catalog=catalog)
                try:
                    w.phase='active'
                    for step in range(120):w.step(FIXED_DT,Controls(1,-1,step%60<40,step<10))
                    self.assertEqual(set(w.mix.values()),{pak+'_'+role for role in CHANNELS})
                finally:w.close()

    def test_enemy_progression_through_public_factory_motion_and_contact_hooks(self):
        for pak in NEW:
            with self.subTest(pak=pak):
                samples=[]
                for level in (1,12,50,101):
                    w=World(Preferences(),24,solo=pak)
                    self.addCleanup(w.close)
                    w.wave=level; w.cover=[]; w.player.pos=Vec(700,220)
                    w.player.health=w.player.max_health=10000
                    part=w.component('enemy')
                    enemy=part.create(w,1000,Vec(100,220)); w.enemies=[enemy]
                    if pak=='canopy_capers':
                        # Measure pursuit speed on actual footing; fixed gravity
                        # and airborne route speeds are reachability constants.
                        enemy.pos.y=480-enemy.radius
                        w.player.pos.y=480-w.player.radius
                    speed=damage=0.
                    for step in range(360):
                        part.advance_enemy(w,enemy,FIXED_DT)
                        if pak!='canopy_capers' or step>=120:
                            speed=max(speed,abs(enemy.vel.x) if pak=='canopy_capers' else enemy.vel.length())
                        w.player.invulnerable=0
                        health=w.player.health
                        part.on_contact(w,enemy,FIXED_DT)
                        damage=max(damage,health-w.player.health)
                    samples.append((enemy.max_health,damage,speed))
                for first,last in zip(samples,samples[1:]):
                    self.assertGreater(last[0],first[0],samples)
                    self.assertGreater(last[1],first[1],samples)
                self.assertGreater(samples[-1][2],samples[0][2],samples)

    def test_actual_directional_launches_prioritize_foreign_pilot_intent_over_targets(self):
        # Placed Ferric rails and contact stomps deliberately do not aim at a
        # supplied pilot heading; test actual aimed projectile launches here.
        for pak in ('rime_rink','storm_loom','kiln_derby','paper_pilgrimage'):
            with self.subTest(weapon=pak):
                world=World(Preferences(),24,solo='orbit_keeper')
                self.addCleanup(world.close)
                world.player.pos=Vec(650,240)
                world.player.vel=Vec()
                world.cover=[]
                world.enemies[0].pos=Vec(350,240)
                world.mix['weapon']=pak
                weapon=world.component('weapon')
                # Real held/released raw input, without calling private aim or
                # fire helpers. Do not advance the projectiles before measuring.
                for _ in range(108):weapon.update(world,FIXED_DT,Controls(fire=True))
                weapon.update(world,FIXED_DT,Controls())
                moving=[s for s in world.projectiles if s.vel.length_squared()>100]
                self.assertTrue(moving,pak)
                for shot in moving:
                    self.assertGreater(shot.vel.normalize().x,.95,pak)

    def test_new_component_imports_stay_role_local_and_use_public_host_services(self):
        for pak in NEW:
            self.assertEqual(set(get_catalog().by_id[pak].parts),set(CHANNELS))
            for role in CHANNELS:
                for path in (ROOT/'paks'/pak/role).glob('*.py'):
                    tree=ast.parse(path.read_text())
                    for node in ast.walk(tree):
                        if isinstance(node,ast.ImportFrom):
                            self.assertLessEqual(node.level,1,str(path))
                            if not node.level and node.module and node.module.startswith('system_panic.'):
                                self.assertIn(node.module,('system_panic.model','system_panic.pak_api'),str(path))
                        if isinstance(node,ast.Import):
                            for alias in node.names:self.assertFalse(alias.name.startswith('paks.'),str(path))

    def test_new_tenth_kill_factories_and_captured_drops_survive_a_weapon_swap(self):
        for pak in NEW:
            with self.subTest(pak=pak):
                w=World(Preferences(),24,solo=pak)
                self.addCleanup(w.close)
                w.kills=9
                w.enemies[0].pos=Vec(100,100)
                w.enemies[0].health=0
                w.remove_dead()
                self.assertEqual(w.kills,10)
                self.assertEqual(len(w.powerups),1)
                drop=w.powerups[0]
                self.assertEqual(drop.pos,Vec(100,100))
                w.mix['weapon']='signal_runner'; w.component('weapon')
                w.player.pos=drop.pos.copy()
                drop.update(w,FIXED_DT)
                self.assertFalse(drop.alive)
                self.assertEqual(w.powerups_collected,1)
                drop.update(w,FIXED_DT)
                self.assertEqual(w.powerups_collected,1)


if __name__=='__main__':unittest.main()
