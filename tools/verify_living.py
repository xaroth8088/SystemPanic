"""Reproducible solo, remix, media and rendering evidence for six Living Paks.

No health/damage/control advantages are supplied to solo samples. Stress mixes
check stability; they are not a universal clearability or human balance claim.
"""
import argparse
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import random
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame
from system_panic.app import App, autopilot
from system_panic.model import Controls
from system_panic.paks import get_catalog, GAMEPLAY_CHANNELS
from system_panic.preferences import Preferences
from system_panic.world import World

PAKS = ('canopy_capers', 'rime_rink', 'storm_loom', 'kiln_derby', 'paper_pilgrimage', 'ferric_ferry')


def media(output):
    import numpy as np
    import soundfile as sf
    records = []
    for pak in PAKS:
        row = dict(pak=pak, images={}, effects={})
        folder = ROOT/'paks'/pak
        metadata=json.loads((folder/'pak.json').read_text())
        for role in ('pilot', 'enemy', 'weapon', 'obstacles'):
            art = pygame.image.load(folder/role/(role+'_sheet.png'))
            columns,rows=metadata['authoring'].get('component_grids',{}).get(role,[4,1])
            assert art.get_width()//columns == art.get_height()//rows, (pak, role)
            hashes = []
            tile=art.get_width()//columns
            for frame in range(columns*rows):
                cell = art.subsurface((frame%columns*tile, frame//columns*tile, tile, tile))
                assert pygame.mask.from_surface(cell, 110).count() > 100
                hashes.append(hashlib.sha256(pygame.image.tostring(cell, 'RGBA')).hexdigest())
            assert len(set(hashes)) == columns*rows, (pak, role, 'animation')
            row['images'][role] = dict(size=art.get_size(), grid=[columns,rows], distinct_frames=len(set(hashes)))
        for role, name in (('pilot', 'special.ogg'), ('weapon', 'shot.ogg')):
            data, sr = sf.read(folder/role/name, always_2d=True)
            assert len(data)/sr > .04 and np.max(np.abs(data)) > .01
            parts = np.array_split(data, 5)
            rms = [float(np.sqrt(np.mean(p*p))) for p in parts]
            row['effects'][role] = dict(seconds=len(data)/sr, tail_to_peak_rms=rms[-1]/max(rms),
                sha256=hashlib.sha256((folder/role/name).read_bytes()).hexdigest())
        data, sr = sf.read(folder/'music/music.ogg', always_2d=True)
        width = sr//10
        peak = max(np.sqrt(np.mean(data[i:i+width]**2)) for i in range(0, len(data)-width, width))
        join = np.concatenate((data[-2*sr:], data[:2*sr]))
        values = [np.sqrt(np.mean(join[i:i+width]**2)) for i in range(0, len(join)-width, width//10)]
        row['music'] = dict(seconds=len(data)/sr, minimum_four_second_join_to_peak_rms=float(min(values)/peak),
            endpoint_step=float(np.max(np.abs(data[0]-data[-1]))))
        assert row['music']['minimum_four_second_join_to_peak_rms'] > .075, row
        records.append(row)
    assert len({r['effects']['pilot']['sha256'] for r in records}) == 6
    assert len({r['effects']['weapon']['sha256'] for r in records}) == 6
    report = dict(paks=records, role_sheets=24, frames=sum(image['distinct_frames'] for r in records for image in r['images'].values()), distinct_specials=6, distinct_shots=6,
                  limits='Decode, animation and cyclic energy checks; no physical speaker listening claim.')
    (output/'media.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f"Media: 24 animated sheets / {report['frames']} distinct frames, twelve distinct effects, six cyclic joins checked.", flush=True)


def solo(args):
    records = []
    for pak, difficulty, seed in itertools.product(PAKS, args.difficulties, args.seeds):
        w = World(Preferences(difficulty=difficulty), seed, solo=pak)
        counts, peak, first_clear = {1:len(w.enemies)}, 0, None
        try:
            for frame in range(args.seconds*60):
                w.advance(1/60, autopilot(w)); w.drain_events()
                if w.wave not in counts:
                    counts[w.wave] = len(w.enemies)
                    assert counts[w.wave] == w.wave
                if first_clear is None and w.phase == 'clear': first_clear = round(frame/60, 3)
                peak = max(peak, len(w.projectiles))
                assert all(math.isfinite(v) for b in (w.player, *w.enemies) for v in (b.pos.x, b.pos.y, b.health))
                if w.phase == 'dead' or w.wave > args.levels: break
            record = dict(pak=pak, difficulty=difficulty, seed=seed, phase=w.phase,
                cleared_levels=w.wave-1+int(w.phase=='clear'), seconds=round(frame/60,3),
                health=round(w.player.health,2), kills=w.kills, upgrades=w.powerups_collected,
                initial_counts=counts, first_clear_seconds=first_clear, max_projectiles=peak)
            records.append(record); print(json.dumps(record), flush=True)
        finally: w.close()
    (args.output/'solo.json').write_text(json.dumps(dict(target=args.levels, input='ordinary digital Controls via Pak demo policies', runs=records), indent=2)+'\n')
    gallery(args.output)
    assert all((r['cleared_levels'] >= args.levels and r['phase']=='active') or
               (args.allow_defeats and r['phase']=='dead') for r in records), 'Inspect failed/defeated/stalled solo samples'


def gallery(output):
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        app = App(Path(temporary), 24)
        try:
            sheet = pygame.Surface((1440, 1212)); sheet.fill((9,16,25))
            for index, pak in enumerate(PAKS):
                app.start(pak); w = app.world
                w.enemies.clear(); w.wave=5; w.start_wave()
                for _ in range(160): app.update(1/60, autopilot(w))
                for _ in range(90):
                    if w.phase=='active' and (w.player.invulnerable<=0 or int(w.time*12)%2): break
                    app.update(1/120, autopilot(w))
                before = (w.time, w.player.pos.copy(), w.rng.getstate(), w.player.health)
                app.draw()
                assert before == (w.time,w.player.pos,w.rng.getstate(),w.player.health)
                pygame.image.save(app.canvas, output/(pak+'.png'))
                x,y = index%2*720,index//2*404
                app.graphics.text(sheet,w.pak('pilot').name,(x+12,y+8),22,w.pak('pilot').color,True)
                sheet.blit(pygame.transform.smoothscale(app.arena_surface,(720,360)),(x,y+40))
            pygame.image.save(sheet,output/'gallery.png')
        finally: app.quit(); pygame.quit()


def mixes(args):
    from verify_frontier_mixes import presentation
    catalog = get_catalog(); old = tuple(p for p in catalog.complete_ids() if p not in PAKS)
    rng = random.Random(6100)
    cases = list(itertools.product(PAKS,repeat=4)); cross=[]
    for index in range(512):
        values=[rng.choice(catalog.complete_ids()) for _ in GAMEPLAY_CHANNELS]
        values[index%4]=rng.choice(PAKS); values[(index+1)%4]=rng.choice(old)
        cross.append(tuple(values))
    peak=swaps=0
    for index, combo in enumerate(cases+cross):
        w=World(Preferences(difficulty='relaxed'),6100,catalog=catalog)
        try:
            w.mix.update(zip(GAMEPLAY_CHANNELS,combo)); w.enemies.clear(); w.wave=2; w.start_wave(); w.phase='active'
            w.powerups_collected=3
            for frame in range(360):
                x,y=math.sin(frame*.04),math.cos(frame*.035)
                w.advance(1/60,Controls((x>.2)-(x<-.2),(y>.2)-(y<-.2),frame%96<72,frame%120<8))
                if frame==180 and index>=len(cases): w.shuffle(); swaps+=1
                assert all(math.isfinite(v) for b in (w.player,*w.enemies) for v in (b.pos.x,b.pos.y,b.health)), combo
                peak=max(peak,len(w.projectiles)); w.drain_events()
        finally: w.close()
        assert not w._geometry
        if (index+1)%128==0: print(f'Mixes {index+1}/{len(cases)+len(cross)} checked',flush=True)
    report=dict(new_gameplay_combinations=len(cases),sampled_old_new_combinations=len(cross),seconds_per_case=6,
        swaps=swaps,max_projectiles=peak,finite_state=True,close_cleans_geometry=True)
    report.update(presentation(catalog))
    (args.output/'mixes.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('solo','mixes','media','all'),default='all')
    parser.add_argument('--levels',type=int,default=6)
    parser.add_argument('--seconds',type=int,default=180)
    parser.add_argument('--allow-defeats',action='store_true',help='Retain legitimate defeats as balance evidence; still reject stalled samples')
    parser.add_argument('--seeds',type=int,nargs='+',default=[24,73,2026])
    parser.add_argument('--difficulties',nargs='+',default=['relaxed','standard'])
    parser.add_argument('--output',type=Path,default=ROOT/'output/living')
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    if args.mode in ('media','all'): media(args.output)
    if args.mode in ('solo','all'): solo(args)
    if args.mode in ('mixes','all'): mixes(args)


if __name__=='__main__': main()
