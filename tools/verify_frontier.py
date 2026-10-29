"""Seed/difficulty balance samples and a rendered gallery for the six new Paks.

Uses ordinary Pak demo controls, without health/aim/damage advantages. The QA
level limit is a stopping point, never an ending in the game. A defeat is recorded
as evidence, not hidden or converted into a pass.
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
from system_panic.app import App, autopilot
from system_panic.preferences import Preferences
from system_panic.world import World

PAKS=('pulse_abbey','scrap_ballet','glasswake','bloom_siege','echo_vault','tidal_choir')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--levels',type=int,default=8)
    parser.add_argument('--seconds',type=int,default=300)
    parser.add_argument('--seeds',type=int,nargs='+',default=[0,24,997])
    parser.add_argument('--difficulties',nargs='+',default=['relaxed','standard'])
    parser.add_argument('--output',type=Path,default=ROOT/'output/frontier')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    records=[]
    for pak in PAKS:
        for difficulty in args.difficulties:
            for seed in args.seeds:
                world=World(Preferences(difficulty=difficulty),seed,solo=pak)
                counts={1:1}
                max_shots=0
                first_clear=None
                for frame in range(args.seconds*60):
                    world.advance(1/60,autopilot(world))
                    world.drain_events()
                    if world.wave not in counts:
                        counts[world.wave]=len(world.enemies)
                        assert counts[world.wave]==world.wave
                    if first_clear is None and world.phase=='clear':first_clear=round(frame/60,2)
                    max_shots=max(max_shots,len(world.projectiles))
                    assert all(math.isfinite(b.pos.x) and math.isfinite(b.pos.y) for b in (world.player,*world.enemies))
                    if world.phase=='dead' or world.wave>args.levels:break
                record=dict(pak=pak,difficulty=difficulty,seed=seed,cleared_levels=world.wave-1+int(world.phase=='clear'),phase=world.phase,
                            health=round(world.player.health,2),seconds=round(frame/60,2),first_clear_seconds=first_clear,
                            kills=world.kills,upgrades=world.powerups_collected,max_projectiles=max_shots,initial_counts=counts)
                records.append(record)
                print(json.dumps(record),flush=True)
                world.close()
    with tempfile.TemporaryDirectory(dir=args.output) as temporary:
        app=App(Path(temporary),24)
        gallery=pygame.Surface((1440,1230))
        gallery.fill((9,16,25))
        for index,pak in enumerate(PAKS):
            app.start(pak)
            w=app.world
            w.enemies.clear()
            w.wave=5
            w.start_wave()
            # Different attack cycles need different capture times: show the
            # pulse after release, a live ray and an ongoing bloom cascade.
            frames={'pulse_abbey':52,'glasswake':80,'bloom_siege':174}.get(pak,150)
            for _ in range(frames):app.update(1/60,autopilot(w))
            # If a scene happened to clear, capture the next actual active level.
            while w.phase=='clear':app.update(1/60,autopilot(w))
            for _ in range(30):
                if w.player.invulnerable<=0 or int(w.time*12)%2:break
                app.update(1/120,autopilot(w))
            app.draw()
            pygame.image.save(app.canvas,args.output/f'{pak}.png')
            x,y=index%2*720,index//2*410
            app.graphics.text(gallery,w.pak('pilot').name,(x+12,y+8),22,w.pak('pilot').color,True)
            app.graphics.text(gallery,w.pak('pilot').subtitle,(x+12,y+34),11,(145,165,180))
            gallery.blit(pygame.transform.scale(app.arena_surface,(720,360)),(x,y+50))
        pygame.image.save(gallery,args.output/'gallery.png')
        app.quit()
        pygame.quit()
    report=dict(target_cleared_levels=args.levels,seconds_limit=args.seconds,input='ordinary Pak demo Controls; no gameplay advantages',
                runtime=sys.version,runs=records)
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Saved {len(records)} measured runs and six rendered scenes; inspect defeats/stalls in report.json.',flush=True)


if __name__=='__main__':main()
