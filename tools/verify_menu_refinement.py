"""Render the quieter menus, complete saved mixes and procedural space effects."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import pygame
from system_panic.app import App
from system_panic.model import Vec
from system_panic.paks import CHANNELS
from system_panic.remixes import Remix
from system_panic.combinations import mix_key
from system_panic.world import World


def verify_menu_refinement(app,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    def screenshot(name):
        app.toast_timer=0;app.draw()
        pygame.image.save(app.canvas,output/('menu-'+name+'.png'))
    app.home()
    for route in ('home','settings','credits','help','remix'):
        app.navigate(route);screenshot(route)
    assert 'mix_mode' not in vars(app.prefs)
    assert pygame.display.get_caption()[0]=='System Panic'
    original_remixes=app.remixes
    providers=list(app.catalog.by_id)
    app.remixes=[Remix('menu_'+str(i),'Sample '+str(i+1),
                      {channel:providers[(i+j)%len(providers)] for j,channel in enumerate(CHANNELS)})
                 for i in range(5)]
    app.remixes[-1].mix['weapon']='missing_weapon'
    flagged=mix_key(app.remixes[2].mix)
    owned_flag=flagged not in app.combination_history.keys
    if owned_flag:assert app.combination_history.flag(app.remixes[2].mix,8,1.25)
    app.navigate('remix-saved')
    labels=[];text=app.graphics.text
    def capture(*args,**kwargs):
        labels.append(str(args[1]));return text(*args,**kwargs)
    try:
        app.graphics.text=capture
        screenshot('saved')
    finally:app.graphics.text=text
    for item in app.remixes[:4]:
        for channel in CHANNELS:
            assert f'{channel.title()}: {app.catalog.by_id[item.mix[channel]].name}' in labels
    assert 'FLAGGED' in labels
    assert len([b for b in app.buttons if b.id.startswith('favorite:')])==4
    app.remix_saved_page=1
    labels.clear();app.graphics.text=capture
    try:screenshot('saved-page-2')
    finally:app.graphics.text=text
    assert 'Weapon: missing_weapon (missing)' in labels and 'UNAVAILABLE' in labels
    assert all(any(label.startswith(channel.title()+':') for label in labels) for channel in CHANNELS)
    assert len([b for b in app.buttons if b.id.startswith('favorite:')])==1
    app.remixes=original_remixes
    if owned_flag:assert app.combination_history.remove(flagged)
    app.start('void_drifter');world:World=app.world;world.phase='active';world.time=8
    world.player.invulnerable=0
    part=world.component('obstacles')
    module=sys.modules[type(part).__module__]
    comet=module.Comet(Vec(740,145),Vec(220,40));comet.age=1.2
    world.cover.append(comet);screenshot('void-drifter')
    gallery=pygame.Surface((1000,520));gallery.fill((9,16,25))
    hole=module.BlackHole(Vec(250,250))
    hole.draw(app.graphics,gallery,world)
    for index,angle in enumerate((0,1.5,3.2)):
        comet.pos=Vec(620+index*120,150+index*100);comet.vel=Vec(220,0).rotate_rad(angle)
        comet.draw(app.graphics,gallery,world)
    pygame.image.save(gallery,output/'menu-void-detail.png')
    # Exercise cold/warm frames without advancing bodies, damage, clocks or RNG.
    surface=pygame.Surface((960,480),pygame.SRCALPHA)
    before=(world.rng.getstate(),part._rng.getstate(),world.player.pos.copy(),world.player.health,
            tuple(comet.pos),tuple(comet.vel),tuple(comet.rect),dict(comet.hits))
    timings=[]
    for frame in range(72):
        world.time=frame/12;comet.age=frame/18
        start=time.perf_counter()
        hole.draw(None,surface,world);comet.draw(None,surface,world)
        timings.append((time.perf_counter()-start)*1000)
    after=(world.rng.getstate(),part._rng.getstate(),world.player.pos.copy(),world.player.health,
           tuple(comet.pos),tuple(comet.vel),tuple(comet.rect),dict(comet.hits))
    assert before==after
    reduced=app.prefs.reduced_motion
    world.prefs.reduced_motion=True
    surface.fill((0,0,0,0));hole.draw(None,surface,world);comet.draw(None,surface,world)
    first=pygame.image.tobytes(surface,'RGBA')
    world.time+=5;comet.age+=4
    surface.fill((0,0,0,0));hole.draw(None,surface,world);comet.draw(None,surface,world)
    assert pygame.image.tobytes(surface,'RGBA')==first
    app.prefs.reduced_motion=reduced
    app.home()
    return dict(saved_components_listed=True,missing_and_flagged_components_listed=True,saved_cards_per_page=4,pagination=True,
                obsolete_style_absent=True,draw_preserves_simulation=True,reduced_motion_static=True,
                effect_draw_ms_max=max(timings),warm_effect_draw_ms_mean=sum(timings[36:])/36)


if __name__=='__main__':
    output=ROOT/'output/verification/menu-refinement'
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as directory:
        app=App(Path(directory),seed=24)
        try:report=verify_menu_refinement(app,output)
        finally:app.quit();pygame.quit()
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
