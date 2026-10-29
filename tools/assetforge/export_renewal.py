"""Register delivered renewal sources and losslessly export animation rows.

Development-only. Missing planned sources are never marked generated. Every
source keeps its original pixels; measured low-alpha row cuts correct the
generator's imperfect nominal grid. Equal padded output frames use API 4.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile
import time

import numpy as np
import pygame

ROOT=Path(__file__).resolve().parents[2]
ROLES=('pilot','enemy','weapon','obstacles')

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def save_png(surface,target):
    # Stage outside the watched Pak directories, then atomically replace only
    # changed bytes. Windows image preview/indexing can briefly hold a target.
    output=ROOT/'output'
    output.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix='.png',dir=output,delete=False) as handle:
        temporary=Path(handle.name)
    try:
        pygame.image.save(surface,temporary)
        if target.exists() and digest(target)==digest(temporary):return
        for attempt in range(4):
            try:
                temporary.replace(target)
                return
            except PermissionError:
                if attempt==3:raise
                time.sleep(.1*(attempt+1))
    finally:temporary.unlink(missing_ok=True)

def copy_audio(jobs):
    records=[]
    for job in jobs:
        manifest=ROOT/f'paks/{job["id"]}/pak.json'
        metadata=json.loads(manifest.read_text()) if manifest.exists() else {}
        for suffix,relative in (('','music/music.ogg'),('_shot','weapon/shot.ogg'),('_special','pilot/special.ogg')):
            source=ROOT/metadata.get('authoring',{}).get('audio_sources',{}).get(relative,f'assets/audio/production/{job["id"]}{suffix}.ogg')
            target=ROOT/f'paks/{job["id"]}/{relative}'
            if not source.exists():raise ValueError('Pending prepared audio: '+str(source))
            # SDL may be streaming an unchanged track in a live game. Avoid
            # reopening its destination for writing when bytes already match.
            if not target.exists() or digest(source)!=digest(target):
                shutil.copyfile(source,target)
            records.append(dict(file=target.relative_to(ROOT).as_posix(),source=source.relative_to(ROOT).as_posix(),operation='Unmodified mastered original local Stable Audio 3 output',sha256=digest(target)))
    return records

def save_records(records):
    path=ROOT/'assets/pak-exports.json'
    old=json.loads(path.read_text(encoding='utf-8'))
    replaced={r['file'] for r in records}
    path.write_text(json.dumps([r for r in old if r['file'] not in replaced]+records,indent=2)+'\n',encoding='utf-8')

def row_bands(atlas):
    alpha=pygame.surfarray.array_alpha(atlas)
    counts=np.sum(alpha>=140,axis=0)
    height=atlas.get_height()
    cuts=[0]
    for index in (1,2,3):
        expected=height*index/4
        low,high=round(expected-height*.065),round(expected+height*.065)
        region=counts[low:high]
        candidates=np.flatnonzero(region<=max(3,int(region.min())))+low
        cut=int(min(candidates,key=lambda y:abs(y-expected)))
        cuts.append(cut)
    cuts.append(height)
    return list(zip(cuts,cuts[1:]))

def register(jobs):
    path=ROOT/'tools/assetforge/image-prompts.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    delivered=[]
    for job in jobs:
        source=ROOT/job['file']
        if not source.exists():continue
        atlas=pygame.image.load(source)
        assert atlas.get_flags()&pygame.SRCALPHA,source
        bands=row_bands(atlas)
        record=dict(id=job['id']+'_renewal',file=job['file'],transparent_background=True,prompt=job['prompt'],
                    actual_geometry=dict(columns=4,row_bands=bands,source_size=atlas.get_size(),note='Low-alpha row boundaries measured from delivered original; lossless cells padded into equal animation frames.'))
        data['jobs']=[old for old in data['jobs'] if old['id']!=record['id']]+[record]
        delivered.append(record)
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    return delivered

def main():
    plan=json.loads((ROOT/'tools/assetforge/renewal-prompts.json').read_text(encoding='utf-8'))
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pak',nargs='+',choices=[j['id'] for j in plan['jobs']])
    parser.add_argument('--register-only',action='store_true')
    parser.add_argument('--audio-only',action='store_true',help='Export prepared audio without changing sprite/runtime metadata')
    args=parser.parse_args()
    selected=[job for job in plan['jobs'] if not args.pak or job['id'] in args.pak]
    if args.audio_only:
        records=copy_audio(selected)
        save_records(records)
        print('Exported',len(records),'local audio copies.',flush=True)
        return
    delivered=register(selected)
    print('Registered',len(delivered),'actual delivered source atlases.',flush=True)
    if args.register_only:return
    if len(delivered)!=len(selected):raise ValueError('Some selected renewal source atlases are still pending generation')
    records=[]
    for job,source_record in zip(selected,delivered):
        source=ROOT/job['file']
        atlas=pygame.image.load(source)
        width=atlas.get_width()
        bands=source_record['actual_geometry']['row_bands']
        metadata=json.loads((ROOT/f'paks/{job["id"]}/pak.json').read_text())
        for role,(top,bottom) in zip(ROLES,bands):
            if role in metadata.get('authoring',{}).get('component_sources',{}):continue
            padding=float(job.get('frame_padding',{}).get(role,1.))
            if not 1<=padding<=2:raise ValueError('Frame padding must be within [1,2]')
            tile=max((width+3)//4,bottom-top)
            sheet=pygame.Surface((tile*4,tile),pygame.SRCALPHA)
            rectangles=[]
            for column in range(4):
                left,right=round(column*width/4),round((column+1)*width/4)
                rect=pygame.Rect(left,top,right-left,bottom-top)
                sheet.blit(atlas.subsurface(rect),(column*tile+(tile-rect.width)//2,(tile-rect.height)//2))
                rectangles.append(tuple(rect))
            common=None
            for column in range(4):
                cell=sheet.subsurface((column*tile,0,tile,tile))
                parts=pygame.mask.from_surface(cell,110).connected_components(250)
                if not parts:raise ValueError('Animation frame has no substantial visible subject')
                bounds=[part.get_bounding_rects()[0] for part in parts]
                bounds=bounds[0].unionall(bounds[1:])
                common=bounds if common is None else common.union(bounds)
            frame_size=math.ceil(max(common.size)*padding)
            registered=pygame.Surface((frame_size*4,frame_size),pygame.SRCALPHA)
            for column in range(4):
                rect=common.move(column*tile,0)
                registered.blit(sheet.subsurface(rect),(column*frame_size+(frame_size-common.width)//2,(frame_size-common.height)//2))
            target=ROOT/f'paks/{job["id"]}/{role}/{role}_sheet.png'
            save_png(registered,target)
            records.append(dict(file=target.relative_to(ROOT).as_posix(),source=job['file'],operation=f'Lossless measured row extraction; common alpha-110/component-250 registration crop {tuple(common)}; four equal {frame_size}px animation frames with padding factor {padding}; source rectangles {rectangles}',sha256=digest(target)))
        # Each background gets its own local decorative texture rather than
        # retaining the original-six shared title-screen image.
        top,bottom=bands[-1]
        bounds=pygame.Rect(0,top,round(width/4),bottom-top)
        decoration=atlas.subsurface(bounds)
        icon=pygame.transform.smoothscale(decoration,(110,110))
        background=pygame.Surface((960,480),pygame.SRCALPHA)
        for row in range(5):
            for column in range(8):
                background.blit(icon,(column*145+(row%2)*65-30,row*125-25))
        target=ROOT/f'paks/{job["id"]}/background/background_image.png'
        save_png(background,target)
        records.append(dict(file=target.relative_to(ROOT).as_posix(),source=job['file'],operation=f'Prepared 960x480 decorative mosaic from first terrain animation cell; source bounds {tuple(bounds)}',sha256=digest(target)))
        records.extend(copy_audio([job]))
        manifest=ROOT/f'paks/{job["id"]}/pak.json'
        data=json.loads(manifest.read_text(encoding='utf-8'))
        data['authoring'].update(animation_grid=[4,4],sheet_source=job['file'])
        data['authoring'].pop('atlas_column',None)
        manifest.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    save_records(records)
    print('Exported',len(records),'self-contained renewal assets.',flush=True)

if __name__=='__main__':main()
