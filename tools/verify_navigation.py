"""Measure a fixed remix at several enemy counts, including real 4K presentation.

Uses ordinary digital Controls and temporary preferences. Optional frozen
verification loads an observer through a temporary external Pak; none is shipped.
No saved favorite or personal preference file is changed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
import pygame
from system_panic.app import App
from system_panic.model import Controls

def exercise(app,case,output,frames=180):
    output=Path(output);output.mkdir(exist_ok=True,parents=True)
    app.prefs.difficulty=case['difficulty'];app.prefs.aim_assist=case['aim_assist']
    app.prefs.render_resolution='3840x2160';app.prefs.fullscreen=False;app.apply_display()
    records=[]
    for level in (1,8,20):
        app.start(fixed_mix=case['mix']);w=app.world;w.enemies.clear();w.wave=level-1;w.start_wave();w.phase='active'
        simulation=[];presentation=[]
        for frame in range(frames):
            controls=Controls(1 if frame%180<90 else -1,-1 if frame%120<6 else 0,frame%150<90)
            start=time.perf_counter();app.update(1/60,controls);simulation.append((time.perf_counter()-start)*1000)
            start=time.perf_counter();app.draw();presentation.append((time.perf_counter()-start)*1000)
        q=lambda xs,p:sorted(xs)[round((len(xs)-1)*p)]
        part=w.component('enemy')
        assert len(part._graphs)<=8
        record=dict(level=level,frames=frames,phase=w.phase,enemies=len(w.enemies),kills=w.kills,
                    update_ms_mean=sum(simulation)/len(simulation),update_ms_p99=q(simulation,.99),
                    presentation_ms_mean=sum(presentation)/len(presentation),presentation_ms_p99=q(presentation,.99),
                    graphs=len(part._graphs),output_size=app.window.get_size())
        records.append(record);print(json.dumps(record),flush=True)
        pygame.image.save(app.canvas,output/f'level-{level}.png')
    return dict(case=case,runs=records,input='ordinary digital Controls, two fixed steps per 60Hz update; no gameplay grants',presentation='actual App.draw/present to a 3840x2160 SDL dummy window; not a physical display benchmark')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',type=Path,default=ROOT/'tests/cases/buggy-remix.json')
    parser.add_argument('--output',type=Path,default=ROOT/'output/buggy-performance/app')
    parser.add_argument('--frames',type=int,default=180)
    parser.add_argument('--frozen',action='store_true')
    args=parser.parse_args();args.output=args.output.resolve();case=json.loads(args.case.read_text());args.output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.output) as tmp:
        app=App(Path(tmp),case['seed'])
        try:report=exercise(app,case,args.output/'source',args.frames)
        finally:app.quit();pygame.quit()
    (args.output/'source.json').write_text(json.dumps(report,indent=2)+'\n')
    if args.frozen:
        with tempfile.TemporaryDirectory(dir=args.output) as tmp:
            tmp=Path(tmp);shutil.copytree(ROOT/'paks',tmp/'paks',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            pilot=tmp/'paks/signal_runner/pilot';shutil.copyfile(Path(__file__),pilot/'_navigation_probe.py')
            hook=f'''
from ._navigation_probe import exercise
from system_panic.app import App
from pathlib import Path
import json,pygame
def _performance_probe(self,*args,**kwargs):
    try:
        report=exercise(self,{case!r},Path({str(args.output/'frozen')!r}),{args.frames})
        Path({str(args.output/'frozen.json')!r}).write_text(json.dumps(report,indent=2))
    finally:
        self.quit();pygame.quit()
App.run=_performance_probe
'''
            entry=pilot/'pilot.py';entry.write_text(entry.read_text(encoding='utf-8')+hook,encoding='utf-8',newline='\n')
            result=subprocess.run([str(ROOT/'dist/SystemPanic/SystemPanic.exe'),'--headless','--pak-dir',str(tmp/'paks'),'--data-dir',str(tmp/'profile'),'--seed',str(case['seed']),'--frames','1'],cwd=tmp,capture_output=True,timeout=90)
            if result.returncode:raise AssertionError(result.stderr.decode(errors='replace'))
            frozen=json.loads((args.output/'frozen.json').read_text());assert len(frozen['runs'])==3
            print('Frozen: exact saved mix, bounded navigation cache, actual 4K presentation passed.',flush=True)

if __name__=='__main__':main()
