"""Lossless export of actual facing grids; component code owns frame selection."""
import ast
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import pygame

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.assetforge.export_renewal import save_png
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def source_cells(size,columns,rows,row_edges=None):
    """Use measured source bands when generated animation rows are uneven."""
    width,height=size
    edges=row_edges if row_edges is not None else [round(row*height/rows) for row in range(rows+1)]
    if (len(edges)!=rows+1 or edges[0]!=0 or edges[-1]!=height
            or any(type(value) is not int for value in edges)
            or any(a>=b for a,b in zip(edges,edges[1:]))):
        raise ValueError('Invalid measured animation row edges')
    return [pygame.Rect(round(column*width/columns),edges[row],
                        round((column+1)*width/columns)-round(column*width/columns),edges[row+1]-edges[row])
            for row in range(rows) for column in range(columns)]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pak',nargs='+',help='Export only these existing jobs')
    args=parser.parse_args()
    plan=json.loads((ROOT/'tools/assetforge/facing-prompts.json').read_text(encoding='utf-8-sig'))
    ledger_path=ROOT/'assets/pak-exports.json';old=json.loads(ledger_path.read_text())
    images_path=ROOT/'tools/assetforge/image-prompts.json';images=json.loads(images_path.read_text())
    records=[];exported=0
    for job in plan['jobs']:
        if args.pak and job['pak'] not in args.pak:continue
        metadata=json.loads((ROOT/f'paks/{job["pak"]}/pak.json').read_text())
        if job.get('role','pilot')=='pilot' and metadata['authoring'].get('pilot_rendering')=='rotated_single':continue
        exported+=1
        source=ROOT/job['file']
        if not source.is_file():raise ValueError('Undelivered facing source '+str(source))
        role=job.get('role','pilot');pak=job['pak'];columns,rows=job['columns'],job['rows']
        # Keep the exact imagegen input when replacing the role's old local row.
        reference=ROOT/f'assets/images/{pak}-pilot-facing-reference.png'
        previous=ROOT/job['reference_file']
        if not reference.exists():
            shutil.copyfile(previous,reference)
            entry=next(r for r in old if r['file']==job['reference_file'])
            records.append(dict(entry,file=reference.relative_to(ROOT).as_posix(),sha256=digest(reference),operation=entry['operation']+'; exact pre-facing input snapshot'))
        atlas=pygame.image.load(source)
        alpha=pygame.surfarray.array_alpha(atlas)
        if not (alpha==0).any():raise ValueError('Facing source is not transparent: '+str(source))
        cells=[];rectangles=[];bounds=[]
        for index,rect in enumerate(source_cells(atlas.get_size(),columns,rows,job.get('source_row_edges'))):
            row,column=divmod(index,columns)
            cell=atlas.subsurface(rect).copy()
            components=pygame.mask.from_surface(cell,110).connected_components(80)
            if not components:raise ValueError('Missing visible facing cell: '+str((pak,row,column)))
            boxes=[m.get_bounding_rects()[0] for m in components]
            bound=boxes[0].unionall(boxes[1:]);cells.append(cell);bounds.append(bound);rectangles.append(tuple(rect))
        # Generated cells can have unequal empty margins. Align each subject's
        # center, while retaining one fixed pixel scale for the entire sheet.
        tile=math.ceil(max(max(b.size) for b in bounds)*(1.02 if pak=='sky_forge' and role=='pilot' else 1.12))
        sheet=pygame.Surface((tile*columns,tile*rows),pygame.SRCALPHA)
        for index,(cell,bound) in enumerate(zip(cells,bounds)):
            crop=bound.clip(cell.get_rect())
            x=(tile-crop.width)//2;y=(tile-crop.height)//2
            if pak=='sky_forge' and role=='pilot':y=tile-1-(bound.bottom-crop.top)
            sheet.blit(cell.subsurface(crop),(index%columns*tile+x,index//columns*tile+y))
        target=ROOT/f'paks/{pak}/{role}/{role}_sheet.png';save_png(sheet,target)
        records.append(dict(file=target.relative_to(ROOT).as_posix(),source=job['file'],operation=f'Lossless {columns}x{rows} cell extraction; per-cell alpha-110/component-80 centered crops {[tuple(b) for b in bounds]}; fixed pixel scale in equal {tile}px frames; source rectangles {rectangles}; Sky pilot foot baseline aligned to frame bottom',sha256=digest(target)))
        entry=dict(id=job['id'],file=job['file'],prompt=job['prompt'],transparent_background=True,reference_file=reference.relative_to(ROOT).as_posix(),reference_sha256=digest(reference),actual_geometry=dict(columns=columns,rows=rows,source_size=atlas.get_size(),source_rectangles=rectangles))
        if job.get('source_row_edges'):entry['actual_geometry']['source_row_edges']=job['source_row_edges']
        images['jobs']=[r for r in images['jobs'] if r['id']!=entry['id']]+[entry]
        manifest=ROOT/f'paks/{pak}/pak.json';meta=json.loads(manifest.read_text())
        meta['authoring'].setdefault('component_sources',{})[role]=job['file']
        meta['authoring'].setdefault('component_grids',{})[role]=[columns,rows]
        manifest.write_text(json.dumps(meta,indent=2)+'\n')
        if role!='pilot':continue
        script=ROOT/f'paks/{pak}/pilot/pilot.py';text=script.read_text();tree=ast.parse(text)
        sprite=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='sprite')
        call=next(n for n in ast.walk(sprite) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='frame')
        handle=ast.unparse(call.func.value)
        lines=text.splitlines();edits=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in ('sprite','sprite_angle','sprite_flip_x')]
        body=['    def sprite(self,world,entity=None):','        actor=entity if entity is not None else (world.player if world is not None else None)','        angle=actor.angle if actor is not None else 0.']
        if columns==2:body+=['        facing=0 if math.cos(angle)>=0 else 1']
        else:body+=[f'        facing=int((angle+math.tau/{columns*2})%math.tau/(math.tau/{columns}))']
        if pak=='neon_breach':body+=['        if actor is not None:','            facing=0 if actor.pos.x<25 else 2 if actor.pos.x>935 else 1 if actor.pos.y<240 else 3']
        body+=['        phase=int((world.time if world is not None else 0)*8)%4']
        if pak=='sky_forge':body+=['        if world is not None:phase=phase%3 if self._grounded else 3']
        body+=[f'        return {handle}.frame(phase*{columns}+facing,columns={columns},rows=4)','','    def sprite_angle(self,world,entity):return 0.','','    def sprite_flip_x(self,world,entity):return False']
        for node in sorted(edits,key=lambda n:n.lineno,reverse=True):lines[node.lineno-1:node.end_lineno]=body if node.name=='sprite' else []
        script.write_text('\n'.join(lines)+'\n')
    replaced={r['file'] for r in records}
    ledger_path.write_text(json.dumps([r for r in old if r['file'] not in replaced]+records,indent=2)+'\n')
    images_path.write_text(json.dumps(images,indent=2)+'\n')
    print('Exported',exported,'actual facing/weapon grids; restored single-pose pilots preserved.')

if __name__=='__main__':main()
