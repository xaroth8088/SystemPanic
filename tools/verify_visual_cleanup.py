"""Capture quiet feedback and all corrected Maze poses at actual game scale."""
import os
from pathlib import Path
import sys
import tempfile
import math

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
import pygame
from system_panic.app import App
from system_panic.model import Controls,Vec

def main():
    output=ROOT/'output/verification/visual-cleanup';output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as directory:
        app=App(Path(directory),seed=24)
        try:
            app.navigate('settings');app.draw();pygame.image.save(app.canvas,output/'settings-final.png')
            app.start('maze_muncher');w=app.world
            gallery=pygame.Surface((640,500));gallery.fill((9,16,25))
            for phase in range(4):
                w.time=(phase+.1)/8
                for facing,name in enumerate(('EAST','SOUTH','WEST','NORTH')):
                    w.player.angle=facing*math.pi/2
                    image=app.graphics.component_sprite(w,'pilot',w.player,88,rotate=False)
                    gallery.blit(image,image.get_rect(center=(80+facing*160,65+phase*115)))
                    if phase==0:app.graphics.text(gallery,name,(80+facing*160,8),13,anchor='midtop')
                    small=app.graphics.component_sprite(w,'pilot',w.player,44,rotate=False)
                    gallery.blit(small,small.get_rect(center=(80+facing*160,104+phase*115)))
            pygame.image.save(gallery,output/'maze-facings-final.png')
            for weapon in ('sky_forge','void_drifter','bloom_siege','maze_muncher'):
                mix=dict.fromkeys(w.mix,'signal_runner');mix['weapon']=weapon
                app.start(fixed_mix=mix);w=app.world;w.phase='active';w.player.pos=Vec(500,240)
                for _ in range(90):w.step(1/120,Controls(fire=True))
                w.player.invulnerable=0
                app.draw();pygame.image.save(app.canvas,output/(weapon+'-readout-final.png'))
        finally:
            app.quit();pygame.quit()

if __name__=='__main__':main()
