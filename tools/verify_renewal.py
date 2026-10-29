"""Repeatable quality/balance samples for the initial twelve Pak refresh.

Ordinary eight-direction controls, no health/resource/damage advantages. A QA
level target is a stopping point, never an ending. Defeats/stalls are evidence.
"""
import argparse
import json
import math
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import pygame
from system_panic.app import App,autopilot
from system_panic.preferences import Preferences
from system_panic.world import World

PAKS=('signal_runner','void_drifter','iron_circuit','sky_forge','phase_garden','orbit_keeper',
      'neon_breach','maze_muncher','burrow_patrol','vector_coil','star_bastion','tide_hopper')

def digital(world):
    control=autopilot(world)
    control.x=int(control.x>.2)-int(control.x<-.2)
    control.y=int(control.y>.2)-int(control.y<-.2)
    return control

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paks',nargs='+',choices=PAKS,default=PAKS)
    parser.add_argument('--seeds',nargs='+',type=int,default=[0,24,997])
    parser.add_argument('--difficulties',nargs='+',default=['relaxed','standard'])
    parser.add_argument('--levels',type=int,default=12)
    parser.add_argument('--seconds',type=int,default=240)
    parser.add_argument('--output',type=Path,default=ROOT/'output/renewal')
    parser.add_argument('--gallery-only',action='store_true')
    args=parser.parse_args()
    args.output.mkdir(exist_ok=True,parents=True)
    records=[]
    for pak in (() if args.gallery_only else args.paks):
        for difficulty in args.difficulties:
            for seed in args.seeds:
                world=World(Preferences(difficulty=difficulty),seed,solo=pak)
                initial={1:1}
                previous_kills=0
                since_kill=max_drought=0
                max_projectiles=0
                for frame in range(args.seconds*60):
                    world.advance(1/60,digital(world))
                    world.drain_events()
                    since_kill=since_kill+1 if world.kills==previous_kills else 0
                    previous_kills=world.kills
                    max_drought=max(max_drought,since_kill)
                    max_projectiles=max(max_projectiles,len(world.projectiles))
                    if world.wave not in initial:
                        initial[world.wave]=len(world.enemies)
                        assert initial[world.wave]==world.wave
                    assert all(math.isfinite(v) for b in (world.player,*world.enemies) for v in (b.pos.x,b.pos.y,b.health))
                    if world.phase=='dead' or world.wave>args.levels:break
                record=dict(pak=pak,difficulty=difficulty,seed=seed,cleared_levels=world.wave-1+int(world.phase=='clear'),phase=world.phase,
                            health=round(world.player.health,2),seconds=round(frame/60,2),kills=world.kills,upgrades=world.powerups_collected,
                            max_projectiles=max_projectiles,max_kill_drought_seconds=round(max_drought/60,2),initial_counts=initial)
                records.append(record)
                print(json.dumps(record),flush=True)
                world.close()
    with tempfile.TemporaryDirectory(dir=args.output) as tmp:
        app=App(Path(tmp),24)
        gallery=pygame.Surface((1920,370*math.ceil(len(args.paks)/3)))
        gallery.fill((8,15,24))
        for index,pak in enumerate(args.paks):
            app.start(pak)
            w=app.world
            w.enemies.clear()
            w.wave=5
            w.start_wave()
            for _ in range(210):app.update(1/60,digital(w))
            while w.phase=='clear':app.update(1/60,digital(w))
            app.draw()
            pygame.image.save(app.canvas,args.output/f'{pak}.png')
            x,y=index%3*640,index//3*370
            app.graphics.text(gallery,w.pak('pilot').name,(x+10,y+8),20,w.pak('pilot').color,True)
            gallery.blit(pygame.transform.scale(app.arena_surface,(640,320)),(x,y+40))
        pygame.image.save(gallery,args.output/'gallery.png')
        app.quit()
        pygame.quit()
    report=dict(target_levels=args.levels,seconds_limit=args.seconds,input='eight digital directions, ordinary Pak demo Controls, no gameplay advantages',runs=records)
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Saved',len(records),'balance samples and gallery. Defeats/stalls remain visible in report.json.',flush=True)

if __name__=='__main__':main()
