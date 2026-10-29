"""Inspect every useful pilot bearing at the actual 44px gameplay size."""
import json
import os
from pathlib import Path
import sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import pygame
from system_panic.graphics import Graphics
from system_panic.model import Vec
from system_panic.preferences import Preferences
from system_panic.world import World

def main():
    pygame.init();pygame.display.set_mode((1,1));graphics=Graphics()
    plan=json.loads((ROOT/'tools/assetforge/facing-prompts.json').read_text(encoding='utf-8-sig'))
    jobs=[j for j in plan['jobs'] if j.get('role','pilot')=='pilot' and json.loads((ROOT/f'paks/{j["pak"]}/pak.json').read_text())['authoring'].get('pilot_rendering')!='rotated_single']
    surface=pygame.Surface((1120,len(jobs)*134));surface.fill((8,18,30));records=[]
    for row,job in enumerate(jobs):
        w=World(Preferences(),24,solo=job['pak']);part=w.component('pilot');c=job['columns']
        graphics.text(surface,job['pak']+'  '+str(c)+' facings',(8,row*134+6),18,(175,215,235))
        pixels=[]
        for phase in range(4):
            w.time=phase/8+.001
            if job['pak']=='sky_forge':part._grounded=phase<3
            for facing in range(c):
                w.player.angle=facing*6.283185307179586/c
                if job['pak']=='neon_breach':
                    w.player.edge=(3,0,1,2)[facing]
                    w.player.pos=Vec([(12,240),(480,12),(948,240),(480,468)][facing])
                image=graphics.component_sprite(w,'pilot',w.player,44)
                assert image.get_bounding_rect(min_alpha=110).height>10
                surface.blit(image,(210+(phase*c+facing)%16*55,row*134+23+(phase*c+facing)//16*51))
                pixels.append(part.sprite(w,w.player).rect[:])
        records.append(dict(pak=job['pak'],facings=c,poses=4,frames=len(pixels),upright=part.sprite_angle(w,w.player)==0))
        w.close()
    target=ROOT/'output/playtest-refinement';target.mkdir(exist_ok=True)
    pygame.image.save(surface,target/'facings.png')
    (target/'facings.json').write_text(json.dumps(records,indent=2)+'\n')
    pygame.quit();print('Rendered',sum(r['frames'] for r in records),'frames across',len(records),'movement-specific pilot sheets.')

if __name__=='__main__':main()
