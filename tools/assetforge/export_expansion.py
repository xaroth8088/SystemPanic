"""Extract new original AI sheets and copy mastered audio into self-contained Paks."""
import hashlib
import json
from pathlib import Path
import shutil

import pygame

ROOT=Path(__file__).resolve().parents[2]


def main():
    records=[]
    for manifest in sorted((ROOT/'paks').glob('*/pak.json')):
        data=json.loads(manifest.read_text(encoding='utf-8'))
        # Four-frame row atlases have their own measured-cell exporter. Do not
        # reinterpret them as this older quadrant layout or overwrite their art.
        if data.get('authoring',{}).get('animation_grid') == [4,4]:continue
        source_name=data.get('authoring',{}).get('sheet_source')
        if not source_name: continue
        source=ROOT/source_name
        atlas=pygame.image.load(source)
        width,height=atlas.get_size()
        groups=[[],[],[],[]]
        # Alpha islands preserve art that extends slightly past a nominal grid line.
        for component in pygame.mask.from_surface(atlas,100).connected_components(250):
            rect=component.get_bounding_rects()[0]
            index=int(rect.centery>=height/2)*2+int(rect.centerx>=width/2)
            groups[index].append(rect)
        sprites={}
        for index,role in enumerate(('pilot','enemy','weapon','obstacles')):
            assert groups[index],(data['id'],role)
            bounds=groups[index][0].unionall(groups[index][1:])
            sprite=atlas.subsurface(bounds).copy()
            sprites[role]=sprite
            target=manifest.parent/role/(role+'_sheet.png')
            pygame.image.save(sprite,target)
            records.append(dict(file=target.relative_to(ROOT).as_posix(),source=source_name,
                                operation=f'Lossless alpha-island crop for {role}; bounds {tuple(bounds)}',
                                sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
        # A prepared decorative mosaic from the original AI obstacle art.
        background=pygame.Surface((960,480),pygame.SRCALPHA)
        tile=pygame.transform.smoothscale(sprites['obstacles'],(130,130))
        for row in range(4):
            for column in range(8): background.blit(tile,(column*140+(row%2)*50-30,row*135-30))
        target=manifest.parent/'background/background_image.png'
        pygame.image.save(background,target)
        records.append(dict(file=target.relative_to(ROOT).as_posix(),source=source_name,
                            operation='Prepared 960x480 decorative mosaic from extracted AI obstacle sprite',
                            sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
        for job,relative in ((data['id'],'music/music.ogg'),(data['id']+'_shot','weapon/shot.ogg'),(data['id']+'_special','pilot/special.ogg')):
            source=ROOT/'assets/audio/production'/(job+'.ogg')
            target=manifest.parent/relative
            shutil.copyfile(source,target)
            records.append(dict(file=target.relative_to(ROOT).as_posix(),source=source.relative_to(ROOT).as_posix(),
                                operation='Unmodified mastered original local Stable Audio 3 output',
                                sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    path=ROOT/'assets/pak-exports.json'
    old=json.loads(path.read_text(encoding='utf-8'))
    replaced={r['file'] for r in records}
    path.write_text(json.dumps([r for r in old if r['file'] not in replaced]+records,indent=2)+'\n',encoding='utf-8')
    print(f'Exported {len(records)} independently owned expansion assets')


if __name__=='__main__': main()
