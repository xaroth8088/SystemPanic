"""Export the delivered Ferric induction-rail artwork; preserve old source art."""
import hashlib
import json
from pathlib import Path
import shutil
import pygame
from export_living_facings import extract
from export_renewal import save_png, save_records

ROOT=Path(__file__).resolve().parents[2]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    job=json.loads(Path(__file__).with_name('living-rail-prompt.json').read_text())
    target=ROOT/'paks/ferric_ferry/weapon/weapon_sheet.png'
    snapshot='assets/images/ferric_ferry-weapon-living-rail-reference.png'
    ledger=json.loads((ROOT/'assets/pak-exports.json').read_text())
    records=[]
    if not (ROOT/snapshot).exists():
        old=next(r for r in ledger if r['file']=='paks/ferric_ferry/weapon/weapon_sheet.png')
        shutil.copyfile(target,ROOT/snapshot)
        records.append(dict(old,file=snapshot,operation=old['operation']+'; exact pre-rail weapon snapshot'))
    atlas=pygame.image.load(ROOT/job['file'])
    sheet,extraction=extract(atlas,4,1)
    save_png(sheet,target)
    records.append(dict(file=target.relative_to(ROOT).as_posix(),source=job['file'],extraction=extraction,
        operation='Lossless four-cell whole-subject induction rail extraction with original-alpha fringe and equal frames',sha256=digest(target)))
    save_records(records)
    prompts_path=Path(__file__).with_name('image-prompts.json');prompts=json.loads(prompts_path.read_text())
    prompts['jobs']=[j for j in prompts['jobs'] if j['id']!=job['id']]+[dict(job,actual_geometry=dict(source_size=atlas.get_size(),extraction=extraction))]
    prompts_path.write_text(json.dumps(prompts,indent=2)+'\n')
    path=ROOT/'paks/ferric_ferry/pak.json';metadata=json.loads(path.read_text())
    metadata['authoring'].setdefault('component_sources',{})['weapon']=job['file']
    metadata['authoring'].setdefault('component_grids',{})['weapon']=[4,1]
    metadata['authoring'].setdefault('component_snapshots',{})['weapon']=snapshot
    path.write_text(json.dumps(metadata,indent=2)+'\n')
    print('Exported four original induction-rail animation frames; orbit artwork archived.')

if __name__=='__main__':main()
