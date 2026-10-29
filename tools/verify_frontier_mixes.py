"""Exercise held/released attacks and swaps beyond the short exhaustive matrix."""
import argparse
import itertools
import json
import math
import os
from pathlib import Path
import random
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
from system_panic.model import Controls
from system_panic.paks import get_catalog, GAMEPLAY_CHANNELS
from system_panic.preferences import Preferences
from system_panic.world import World

NEW=('pulse_abbey','scrap_ballet','glasswake','bloom_siege','echo_vault','tidal_choir')


def presentation(catalog):
    import pygame
    from system_panic.app import App
    pairs=0
    with tempfile.TemporaryDirectory(dir=ROOT/'output') as temporary:
        app=App(Path(temporary),101,catalog)
        try:
            app.start(catalog.complete_ids()[0])
            for background,music in itertools.product(catalog.providers('background'),catalog.providers('music')):
                w=app.world
                w.mix.update(background=background,music=music)
                w.component('background')
                track=w.component('music').track(w)
                app.audio.music(track)
                before=(w.time,w.player.pos.copy(),w.rng.getstate())
                app.draw()
                assert before==(w.time,w.player.pos,w.rng.getstate())
                assert app.audio.current==track.path
                pairs+=1
        finally:
            app.quit()
            pygame.quit()
    return dict(presentation_pairs_checked=pairs,read_only_render=True,local_music_streams=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--presentation-only',action='store_true')
    args=parser.parse_args()
    catalog=get_catalog()
    if args.presentation_only:
        report=presentation(catalog)
        (ROOT/'output/frontier-presentation.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),flush=True)
        return
    cases=list(itertools.product(NEW,repeat=4))
    rng=random.Random(101)
    old=tuple(p for p in catalog.complete_ids() if p not in NEW)
    cross=[]
    for index in range(256):
        providers=[rng.choice(catalog.complete_ids()) for _ in GAMEPLAY_CHANNELS]
        providers[index%4]=rng.choice(NEW)
        providers[(index+1)%4]=rng.choice(old)
        cross.append(tuple(providers))
    checks=swaps=0
    maximum=0
    for index,combo in enumerate(cases+cross):
        w=World(Preferences(difficulty='relaxed'),101,catalog=catalog)
        w.mix.update(zip(GAMEPLAY_CHANNELS,combo))
        w.enemies.clear()
        w.wave=1
        w.start_wave()
        w.phase='active'
        for frame in range(240):
            # Deliberate release edges exercise charging, cascading and launch.
            x,y=math.sin(frame*.04),math.cos(frame*.035)
            c=Controls((x>.2)-(x<-.2),(y>.2)-(y<-.2),frame%96<72,frame%120<8)
            w.advance(1/60,c)
            if frame==120 and index>=len(cases):
                w.shuffle()
                swaps+=1
            assert all(math.isfinite(value) for b in (w.player,*w.enemies) for value in (b.pos.x,b.pos.y,b.health))
            maximum=max(maximum,len(w.projectiles))
            w.drain_events()
        w.close()
        assert not w._geometry
        checks+=1
        if checks%128==0:print(f'{checks}/{len(cases)+len(cross)} release-cycle cases; no failures',flush=True)
    report=dict(new_gameplay_combinations=len(cases),sampled_cross_generation_combinations=len(cross),
                seconds_per_case=4,mid_cycle_swaps=swaps,finite_state=True,close_releases_geometry=True,
                max_projectiles=maximum,seed=101)
    report.update(presentation(catalog))
    output=ROOT/'output/frontier-mixes.json'
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
