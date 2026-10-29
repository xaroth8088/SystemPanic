"""Register delivered true actor turnarounds; keep every connected silhouette.

Development only. Whole-atlas subjects are mapped to the intended direction /
animation cell by center. They are never clipped at nominal cell boundaries.
"""
import ast
import hashlib
import json
from pathlib import Path
import math

import numpy as np
import pygame
from export_renewal import save_png, save_records

ROOT=Path(__file__).resolve().parents[2]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(atlas, columns, rows, *, grounded=False, source_columns=None):
    parts=pygame.mask.from_surface(atlas,110).connected_components(60)
    parts.sort(key=lambda part:part.count(),reverse=True)
    count=columns*rows
    if len(parts)<count:raise ValueError(f'Expected {count} complete subjects; found {len(parts)}')
    cores=parts[:count]
    boxes=[part.get_bounding_rects()[0] for part in cores]
    cells={}
    for index,box in enumerate(boxes):
        key=(min(rows-1,box.centery*rows//atlas.get_height()),min(columns-1,box.centerx*columns//atlas.get_width()))
        if key in cells:raise ValueError(f'Multiple large subjects in {key}: grid needs inspection')
        cells[key]=index
    visible=pygame.mask.from_surface(atlas,16).connected_components(30)
    groups=[[] for _ in cores]
    for part in visible:
        box=part.get_bounding_rects()[0]
        overlaps=[i for i,core in enumerate(cores) if part.overlap(core,(0,0)) is not None]
        if len(overlaps)>1:raise ValueError('Visible glow connects multiple facing subjects')
        def distance(i):
            b=boxes[i]
            return (max(0,b.left-box.right,box.left-b.right)**2+max(0,b.top-box.bottom,box.top-b.bottom)**2,
                    (b.centerx-box.centerx)**2+(b.centery-box.centery)**2)
        owner=overlaps[0] if overlaps else min(range(count),key=distance)
        groups[owner].append(part)
    owners=np.zeros(atlas.get_size(),np.uint8)
    for index,group in enumerate(groups):
        for part in group:
            box=part.get_bounding_rects()[0]
            mask=pygame.Mask(box.size);mask.draw(part,(-box.x,-box.y))
            selected=pygame.surfarray.array_alpha(mask.to_surface(setcolor=(255,255,255,255),unsetcolor=(0,0,0,0)))>0
            owners[box.left:box.right,box.top:box.bottom][selected]=index+1
    for _ in range(2):
        expanded=owners.copy()
        for dx,dy in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
            sx=slice(max(0,-dx),min(atlas.get_width(),atlas.get_width()-dx));sy=slice(max(0,-dy),min(atlas.get_height(),atlas.get_height()-dy))
            tx=slice(max(0,dx),min(atlas.get_width(),atlas.get_width()+dx));ty=slice(max(0,dy),min(atlas.get_height(),atlas.get_height()+dy))
            old,target=owners[sx,sy],expanded[tx,ty]
            fill=(target==0)&(old>0);target[fill]=old[fill]
        owners=expanded
    frames=[];records=[]
    for row in range(rows):
        for col in range(columns):
            source_col=source_columns[row][col] if source_columns is not None else col
            index=cells[(row,source_col)]
            bounds=[p.get_bounding_rects()[0] for p in groups[index]]
            crop=bounds[0].unionall(bounds[1:]).inflate(4,4).clip(atlas.get_rect())
            image=atlas.subsurface(crop).copy()
            excluded=owners[crop.left:crop.right,crop.top:crop.bottom]!=index+1
            alpha=pygame.surfarray.pixels_alpha(image);alpha[excluded]=0;del alpha
            rgb=pygame.surfarray.pixels3d(image);rgb[excluded]=0;del rgb
            frames.append(image)
            records.append(dict(row=row,column=col,source_column=source_col,source_bounds=list(crop),core_bounds=list(boxes[index]),
                visible_component_bounds=[list(b) for b in bounds],core_pixels=cores[index].count(),fringe_pixels=2))
    tile=math.ceil(max(max(frame.get_size()) for frame in frames)*1.05)+4
    sheet=pygame.Surface((columns*tile,rows*tile),pygame.SRCALPHA)
    for index,(frame,record) in enumerate(zip(frames,records)):
        x=index%columns*tile+(tile-frame.get_width())//2
        y=index//columns*tile+(tile-frame.get_height()-2 if grounded else (tile-frame.get_height())//2)
        sheet.blit(frame,(x,y));record['destination_bounds']=[x,y,*frame.get_size()]
    return sheet,records


def update_sprite(path,role,columns):
    source=path.read_text();tree=ast.parse(source)
    sprite=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='sprite')
    call=next(n for n in ast.walk(sprite) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='frame')
    handle=ast.unparse(call.func.value)
    actor='entity if entity is not None else (world.player if world is not None else None)' if role=='pilot' else 'entity'
    body=['    def sprite(self, world, entity=None):',f'        actor={actor}',
          '        angle=actor.angle if actor is not None else 0.']
    body+=['        facing=0 if math.cos(angle)>=0 else 1'] if columns==2 else [f'        facing=int((angle+math.tau/{columns*2})%math.tau/(math.tau/{columns}))']
    body+=['        phase=int((world.time if world is not None else 0)*8)%4',
          f'        return {handle}.frame(phase*{columns}+facing, columns={columns}, rows=4)',
          '', '    def sprite_angle(self,world,entity):return 0.', '', '    def sprite_flip_x(self,world,entity):return False']
    nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in ('sprite','sprite_angle','sprite_flip_x')]
    lines=source.splitlines()
    for node in sorted(nodes,key=lambda n:n.lineno,reverse=True):lines[node.lineno-1:node.end_lineno]=body if node.name=='sprite' else []
    path.write_text('\n'.join(lines)+'\n')


def main():
    plan=json.loads(Path(__file__).with_name('living-facing-prompts.json').read_text())
    prompts_path=Path(__file__).with_name('image-prompts.json');prompts=json.loads(prompts_path.read_text())
    records=[]
    for job in plan['jobs']:
        source=ROOT/job['file'];atlas=pygame.image.load(source)
        sheet,extraction=extract(atlas,job['columns'],job['rows'],grounded=job['pak']=='canopy_capers',source_columns=job.get('source_columns'))
        target=ROOT/f'paks/{job["pak"]}/{job["role"]}/{job["role"]}_sheet.png'
        save_png(sheet,target)
        records.append(dict(file=target.relative_to(ROOT).as_posix(),source=job['file'],sha256=digest(target),
            operation='Lossless true directional/animation subject extraction with exclusive visible-glow ownership, original RGBA fringe and equal padded frames; no resampling',extraction=extraction))
        prompts['jobs']=[j for j in prompts['jobs'] if j['id']!=job['id']]+[dict(job,transparent_background=True,actual_geometry=dict(size=atlas.get_size(),extraction=extraction))]
        manifest=ROOT/f'paks/{job["pak"]}/pak.json';metadata=json.loads(manifest.read_text())
        metadata['authoring'].setdefault('component_sources',{})[job['role']]=job['file']
        metadata['authoring'].setdefault('component_grids',{})[job['role']]=[job['columns'],job['rows']]
        manifest.write_text(json.dumps(metadata,indent=2)+'\n')
        update_sprite(ROOT/f'paks/{job["pak"]}/{job["role"]}/{job["role"]}.py',job['role'],job['columns'])
    prompts_path.write_text(json.dumps(prompts,indent=2)+'\n');save_records(records)
    print(f'Exported {len(records)} actual actor facing sheets.')


if __name__=='__main__':main()
