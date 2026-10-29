"""Longer held/released and replacement checks for the initial twelve renewal.

These are compatibility/stability samples. Awkward mixes need not clear.
"""
import itertools
import json
import math
import os
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
from system_panic.model import Controls
from system_panic.paks import get_catalog,GAMEPLAY_CHANNELS
from system_panic.preferences import Preferences
from system_panic.world import World
from verify_renewal import PAKS

def main():
    catalog=get_catalog()
    rng=random.Random(2718)
    cases=[]
    for index,(pilot,weapon) in enumerate(itertools.product(PAKS,repeat=2)):
        cases.append((pilot,PAKS[index%12],weapon,PAKS[(index//12+index)%12]))
    for _ in range(512):cases.append(tuple(rng.choice(catalog.complete_ids()) for _ in GAMEPLAY_CHANNELS))
    peak=swaps=0
    for index,combo in enumerate(cases):
        w=World(Preferences(difficulty='relaxed'),2718,catalog=catalog)
        try:
            w.mix.update(zip(GAMEPLAY_CHANNELS,combo))
            w.enemies.clear()
            w.wave=3
            w.start_wave()
            w.phase='active'
            w.powerups_collected=index%13
            for frame in range(360):
                control=Controls(int(math.sin(frame*.025)>.2)-int(math.sin(frame*.025)<-.2),
                                 int(math.cos(frame*.04)>.2)-int(math.cos(frame*.04)<-.2),frame%210<156,frame%180<6)
                w.advance(1/60,control)
                if frame==180 and index>=144:
                    w.shuffle();swaps+=1
                assert all(math.isfinite(v) for body in (w.player,*w.enemies) for v in (body.pos.x,body.pos.y,body.health)),combo
                assert len(w.projectiles)<512,combo
                peak=max(peak,len(w.projectiles))
                w.drain_events()
        finally:w.close()
        assert not w._geometry,combo
        if (index+1)%100==0:print(f'{index+1}/{len(cases)} compatibility cases',flush=True)
    report=dict(cases=len(cases),all_renewed_pilot_weapon_pairs=144,seeded_cross_pak_cases=512,
                frames_per_case=360,swaps=swaps,peak_projectiles=peak,finite_state=True,owned_geometry_released=True,
                scope='Stability and lifecycle, not a claim that every mix clears')
    (ROOT/'output/renewal-mixes.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
