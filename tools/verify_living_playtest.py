"""Capture all new true bearings plus actual revised gameplay for inspection."""
import json
import os
from pathlib import Path
import sys
import tempfile
import math

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import pygame
from system_panic.app import App,autopilot


def exercise(app,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    jobs=json.loads((ROOT/'tools/assetforge/living-facing-prompts.json').read_text())['jobs']
    gallery=pygame.Surface((1100,len(jobs)*132));gallery.fill((9,16,25))
    checks=0
    for row,job in enumerate(jobs):
        app.start(job['pak']);w=app.world
        actor=w.player if job['role']=='pilot' else w.enemies[0]
        part=w.component(job['role']);w.time=.26
        y=row*132
        app.graphics.text(gallery,job['pak'].replace('_',' ')+' / '+job['role'],(12,y+8),16,(180,210,225))
        before=w.rng.getstate()
        for facing in range(job['columns']):
            angle=facing*math.tau/job['columns'];actor.angle=angle
            handle=part.sprite(w,actor)
            x=12+facing*134
            small=app.graphics.render_sprite(handle,44,(220,235,245))
            large=app.graphics.render_sprite(handle,88,(220,235,245))
            gallery.blit(small,(x,y+50));gallery.blit(large,(x+44,y+36))
            app.graphics.text(gallery,str(round(math.degrees(angle)))+' deg',(x,y+114),11,(130,160,177))
            assert part.sprite_angle(w,actor)==0 and not part.sprite_flip_x(w,actor)
            checks+=1
        assert w.rng.getstate()==before
    pygame.image.save(gallery,output/'bearings.png')
    scenes=pygame.Surface((1440,1212));scenes.fill((9,16,25))
    for index,pak in enumerate(dict.fromkeys(j['pak'] for j in jobs)):
        app.start(pak);w=app.world
        w.enemies.clear();w.wave=5;w.start_wave()
        for _ in range(180):app.update(1/60,autopilot(w))
        for _ in range(120):
            if w.phase=='active' and (w.player.invulnerable<=0 or int(w.time*12)%2):break
            app.update(1/120,autopilot(w))
        before=(w.time,w.rng.getstate(),w.player.pos.copy(),w.player.health)
        app.draw()
        assert before==(w.time,w.rng.getstate(),w.player.pos,w.player.health)
        pygame.image.save(app.canvas,output/(pak+'.png'))
        x,y=index%2*720,index//2*404
        app.graphics.text(scenes,w.pak('pilot').name,(x+12,y+8),22,w.pak('pilot').color,True)
        scenes.blit(pygame.transform.smoothscale(app.arena_surface,(720,360)),(x,y+40))
    pygame.image.save(scenes,output/'gameplay.png')
    report=dict(actual_bearing_selections=checks,actor_sheets=len(jobs),no_rotation_or_mirror_substitute=True,
        presentation_preserves_rng=True,input='ordinary demo Controls',staged_level=6)
    (output/'renders.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    output=ROOT/'output/living-playtest/rendered';output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        app=App(Path(temporary),24)
        try:print(json.dumps(exercise(app,output)))
        finally:app.quit();pygame.quit()


if __name__=='__main__':main()
