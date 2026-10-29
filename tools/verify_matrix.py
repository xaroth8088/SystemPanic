"""Run the exhaustive unit gameplay matrix with read-only PNG decode caching.

Every World/component/gameplay state is fresh. Only immutable source image
pixels are cached, avoiding repeated disk decoding in a simulation-only test.
Asset/frame/rendering correctness is checked separately by the asset tests.
"""
import functools
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import itertools
import json
import os
from pathlib import Path
import sys
import subprocess
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
sys.path.insert(0,str(ROOT/'src'))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import pygame
from test_world import WorldTests,PAKS
from system_panic.world import World

def worker(index,count):
    cached=functools.lru_cache(maxsize=None)(pygame.image.load)
    start=time.perf_counter()
    original=World.__init__
    product=itertools.product
    total=len(PAKS)**4
    expected=len(range(index,total,count))
    def partitioned(*args,**kwargs):
        values=product(*args,**kwargs)
        if len(args)==1 and args[0] is PAKS and kwargs==dict(repeat=4):
            return itertools.islice(values,index,None,count)
        return values
    created=0
    def counted(self,*args,**kwargs):
        nonlocal created
        original(self,*args,**kwargs)
        created+=1
        if created%5000==0:print(f'{created}/{expected} fresh worlds; {time.perf_counter()-start:.1f}s',flush=True)
    suite=unittest.TestSuite([WorldTests('test_all_component_mixes_update_and_fire_safely')])
    with patch.object(pygame.image,'load',cached),patch.object(World,'__init__',counted),patch.object(itertools,'product',partitioned):
        result=unittest.TextTestRunner(verbosity=2).run(suite)
    info=cached.cache_info()
    passed=result.wasSuccessful() and created==expected
    report=dict(worker=index,workers=count,tests=result.testsRun,combinations=expected,
                fixed_steps_per_mix=20,seconds=round(time.perf_counter()-start,3),
                passed=passed,exit_code=int(not passed),
                fresh_gameplay_instances=True,worlds_created=created,decode_cache=dict(hits=info.hits,misses=info.misses),
                scope='Unmodified test assertions; deterministic disjoint product-index partition; cached read-only PNG pixels')
    (ROOT/f'output/renewal-matrix-worker-{index}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
    return report['exit_code']

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers',type=int,default=4,choices=range(1,9))
    parser.add_argument('--worker-index',type=int)
    args=parser.parse_args()
    if args.worker_index is not None:raise SystemExit(worker(args.worker_index,args.workers))
    start=time.perf_counter()
    def run(index):
        with (ROOT/f'output/renewal-matrix-worker-{index}.log').open('w') as log:
            completed=subprocess.run([sys.executable,'-u',str(Path(__file__).resolve()),'--workers',str(args.workers),'--worker-index',str(index)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        record=json.loads((ROOT/f'output/renewal-matrix-worker-{index}.json').read_text())
        assert completed.returncode==record['exit_code']
        return record
    results=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(run,i) for i in range(args.workers)]):
            row=future.result();results.append(row)
            print(f"Worker {row['worker']}: {row['worlds_created']} fresh worlds; passed={row['passed']}",flush=True)
    total=len(PAKS)**4
    covered={i for row in results for i in range(row['worker'],total,args.workers)}
    assert covered==set(range(total)) and sum(row['combinations'] for row in results)==total
    passed=all(row['passed'] for row in results)
    report=dict(command='python tools/verify_matrix.py',tests=1,workers=args.workers,combinations=total,
                fixed_steps_per_mix=20,seconds=round(time.perf_counter()-start,3),passed=passed,exit_code=int(not passed),
                fresh_gameplay_instances=True,worlds_created=sum(row['worlds_created'] for row in results),
                disjoint_full_coverage=True,results=sorted(results,key=lambda row:row['worker']),
                scope='Original unittest assertions and full product space, disjoint worker partitions; cached read-only PNG decoding')
    (ROOT/'output/renewal-matrix.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
    raise SystemExit(report['exit_code'])

if __name__=='__main__':main()
