"""Losslessly slice the six four-frame AI atlases; export locally mastered audio.

This development command never runs in the game. Explicit IDs keep it from
reinterpreting older atlas layouts. Source geometry is measured, not assumed.
"""
import hashlib
import json
from pathlib import Path
import shutil

import pygame

ROOT=Path(__file__).resolve().parents[2]
PAKS=('pulse_abbey','scrap_ballet','glasswake','bloom_siege','echo_vault','tidal_choir')


def main():
    records=[]
    for pak in PAKS:
        metadata=json.loads((ROOT/f'paks/{pak}/pak.json').read_text())
        source=ROOT/f'assets/images/{pak}-source.png'
        atlas=pygame.image.load(source)
        width,height=atlas.get_size()
        tile=max((width+3)//4,(height+3)//4)
        for row,role in enumerate(('pilot','enemy','weapon','obstacles')):
            if role in metadata.get('authoring',{}).get('component_sources',{}):continue
            sheet=pygame.Surface((tile*4,tile),pygame.SRCALPHA)
            bounds=[]
            for col in range(4):
                rect=pygame.Rect(round(col*width/4),round(row*height/4),round((col+1)*width/4)-round(col*width/4),round((row+1)*height/4)-round(row*height/4))
                sheet.blit(atlas.subsurface(rect),(col*tile+(tile-rect.width)//2,(tile-rect.height)//2))
                bounds.append(tuple(rect))
            destination=ROOT/'paks'/pak/role/(role+'_sheet.png')
            pygame.image.save(sheet,destination)
            records.append(dict(file=destination.relative_to(ROOT).as_posix(),source=source.relative_to(ROOT).as_posix(),operation=f'Lossless row/cell extraction into four equal {tile}px padded animation frames; source rectangles {bounds}',sha256=hashlib.sha256(destination.read_bytes()).hexdigest()))
        for suffix,relative in (('','music/music.ogg'),('_shot','weapon/shot.ogg'),('_special','pilot/special.ogg')):
            source=ROOT/f'assets/audio/production/{pak}{suffix}.ogg'
            destination=ROOT/'paks'/pak/relative
            shutil.copyfile(source,destination)
            records.append(dict(file=destination.relative_to(ROOT).as_posix(),source=source.relative_to(ROOT).as_posix(),operation='Unmodified mastered original offline Stable Audio 3 generation',sha256=hashlib.sha256(destination.read_bytes()).hexdigest()))
    ledger=ROOT/'assets/pak-exports.json'
    old=json.loads(ledger.read_text())
    replaced={r['file'] for r in records}
    ledger.write_text(json.dumps([r for r in old if r['file'] not in replaced]+records,indent=2)+'\n')
    sheets=sum(r['file'].endswith('_sheet.png') for r in records)
    print(f'Exported {len(records)} role-local assets, including {sheets} four-frame animation sheets; role source overrides preserved.')


if __name__=='__main__':main()
