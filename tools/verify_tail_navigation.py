"""Paired fixed-mix route timings with ordinary driving/fire input."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
from system_panic.world import World
from system_panic.model import Controls,FIXED_DT
from system_panic.preferences import Preferences

def exercise(seconds):
    case=json.loads((ROOT/'tests/cases/iron-maze-tail.json').read_text())
    records=[]
    for level in (1,8,20):
        world=World(Preferences(difficulty=case['difficulty']),case['seed'],fixed_mix=case['mix'])
        world.enemies.clear();world.wave=level-1;world.start_wave();world.phase='active'
        elapsed=[];peak_segments=peak_areas=0
        for step in range(round(seconds/FIXED_DT)):
            before=time.perf_counter()
            world.step(FIXED_DT,Controls(x=1,fire=True))
            elapsed.append((time.perf_counter()-before)*1000)
            weapon=world.component('weapon')
            peak_segments=max(peak_segments,len(weapon._points)-1)
            peak_areas=max(peak_areas,len(weapon._areas))
        weapon=world.component('weapon')
        state=dict(player=(tuple(world.player.pos),tuple(world.player.vel),world.player.health,world.player.angle),
                   enemies=[(e.id,tuple(e.pos),tuple(e.vel),e.health,e.age) for e in world.enemies],
                   points=[tuple(p) for p in weapon._points],kills=world.kills,score=world.score,
                   phase=world.phase,time=world.time,rng=repr(world.rng.getstate()))
        record=dict(level=level,steps=len(elapsed),mean_ms=sum(elapsed)/len(elapsed),
                    p99_ms=sorted(elapsed)[round((len(elapsed)-1)*.99)],max_ms=max(elapsed),
                    tail_segments=max(0,len(weapon._points)-1),enemies=len(world.enemies),
                    peak_segments=peak_segments,peak_areas=peak_areas,
                    phase=world.phase,state_sha256=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest())
        records.append(record);print(json.dumps(record),flush=True);world.close()
    return dict(case=case,runs=records,seconds=seconds,input='ordinary Controls(x=1, fire=True), no gameplay grants')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',default='after')
    parser.add_argument('--seconds',type=float,default=2)
    args=parser.parse_args()
    output=ROOT/'output/tail-navigation';output.mkdir(parents=True,exist_ok=True)
    report=exercise(args.seconds)
    (output/(args.label+'.json')).write_text(json.dumps(report,indent=2)+'\n')
