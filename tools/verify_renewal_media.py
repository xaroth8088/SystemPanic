"""Audit local renewal animation/effects and encoded cyclic music energy."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pygame
import soundfile as sf
from verify_renewal import PAKS

ROOT=Path(__file__).resolve().parents[1]

def main():
    records=[]
    for pak in PAKS:
        folder=ROOT/'paks'/pak
        metadata=json.loads((folder/'pak.json').read_text())
        row=dict(pak=pak,images={},effects={})
        for role in ('pilot','enemy','weapon','obstacles'):
            path=folder/role/(role+'_sheet.png')
            art=pygame.image.load(path)
            columns,rows=metadata['authoring'].get('component_grids',{}).get(role,[4,1])
            if columns*rows>1:assert art.get_width()//columns==art.get_height()//rows,(pak,role)
            row['images'][role]=dict(size=art.get_size(),grid=[columns,rows],frames=columns*rows,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        for role,file in (('pilot','special.ogg'),('weapon','shot.ogg')):
            path=folder/role/file
            row['effects'][role]=hashlib.sha256(path.read_bytes()).hexdigest()
        data,sr=sf.read(folder/'music/music.ogg',always_2d=True)
        width=sr//10
        rms=np.array([np.sqrt(np.mean(data[i:i+width]**2)) for i in range(0,len(data)-width+1,width)])
        cyclic=np.concatenate((data[-sr:],data[:sr]))
        joins=[np.sqrt(np.mean(cyclic[i:i+width]**2)) for i in range(len(cyclic)//2-width,len(cyclic)//2+1,width//10)]
        ratio=float(min(joins)/max(rms))
        assert ratio>.075,(pak,ratio)
        row['music']=dict(seconds=len(data)/sr,minimum_cyclic_join_to_peak_rms=ratio,
                          endpoint_step=float(np.max(np.abs(data[0]-data[-1]))))
        if pak=='neon_breach':
            whole_join=np.concatenate((data[-2*sr:],data[:2*sr]))
            values=[np.sqrt(np.mean(whole_join[i:i+width]**2)) for i in range(0,len(whole_join)-width,width//10)]
            whole_ratio=float(min(values)/np.sqrt(np.mean(data[sr:-sr]**2)))
            assert whole_ratio>.3,whole_ratio
            row['music']['minimum_four_second_join_to_interior_rms']=whole_ratio
        records.append(row)
    report=dict(paks=records,role_sheets=48,animated_role_sheets=sum(s['frames']>1 for r in records for s in r['images'].values()),frames=sum(s['frames'] for r in records for s in r['images'].values()),
                unique_special_effects=len({r['effects']['pilot'] for r in records}),
                unique_attack_effects=len({r['effects']['weapon'] for r in records}),
                all_encoded_music_joins_above_energy_floor=True,
                limit='Energy and decoding checks do not establish subjective musical quality')
    (ROOT/'output/renewal-media.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:value for key,value in report.items() if key!='paks'}))

if __name__=='__main__':main()
