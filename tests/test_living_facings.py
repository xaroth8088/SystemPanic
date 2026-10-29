"""Real directional cells, intact source pixels and read-only presentation."""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import pygame
from system_panic.preferences import Preferences
from system_panic.world import World


class LivingFacingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jobs=json.loads((ROOT/'tools/assetforge/living-facing-prompts.json').read_text())['jobs']
        cls.manifest={r['file']:r for r in json.loads((ROOT/'assets/manifest.json').read_text())['assets']}

    def test_every_actual_direction_and_animation_cell_is_selected_without_rotation_or_mirroring(self):
        count=0
        for job in self.jobs:
            w=World(Preferences(),24,solo=job['pak'])
            try:
                part=w.component(job['role']);actor=w.player if job['role']=='pilot' else w.enemies[0]
                art=pygame.image.load(ROOT/f"paks/{job['pak']}/{job['role']}/{job['role']}_sheet.png")
                tile=art.get_width()//job['columns']
                self.assertEqual(art.get_height(),job['rows']*tile)
                rng=w.rng.getstate()
                for row in range(job['rows']):
                    w.time=(row+.01)/8
                    for column in range(job['columns']):
                        actor.angle=column*math.tau/job['columns']
                        sprite=part.sprite(w,actor)
                        self.assertEqual(tuple(sprite.rect),(column*tile,row*tile,tile,tile),job['id'])
                        self.assertEqual(part.sprite_angle(w,actor),0,job['id'])
                        self.assertFalse(part.sprite_flip_x(w,actor),job['id'])
                        self.assertGreater(pygame.mask.from_surface(art.subsurface(sprite.rect),110).count(),80)
                        count+=1
                self.assertEqual(w.rng.getstate(),rng)
            finally:w.close()
        self.assertEqual(count,336)

    def test_whole_directional_source_subjects_survive_without_sibling_leakage(self):
        total=0
        for job in self.jobs:
            atlas=pygame.image.load(ROOT/job['file'])
            path=f"paks/{job['pak']}/{job['role']}/{job['role']}_sheet.png"
            record=self.manifest[path]
            sheet=pygame.image.load(ROOT/path)
            parts=pygame.mask.from_surface(atlas,16).connected_components(30)
            by_bounds={tuple(p.get_bounding_rects()[0]):p for p in parts}
            covered=pygame.Mask(atlas.get_size())
            for frame in record['extraction']:
                bounds=pygame.Rect(frame['source_bounds'])
                image=sheet.subsurface(pygame.Rect(frame['destination_bounds']))
                actual=pygame.image.tobytes(image,'RGBA')
                original=pygame.image.tobytes(atlas.subsurface(bounds),'RGBA')
                selected={tuple(box) for box in frame['visible_component_bounds']}
                for box,part in by_bounds.items():
                    if not bounds.colliderect(pygame.Rect(box)):continue
                    local=pygame.Mask(bounds.size);local.draw(part,(-bounds.x,-bounds.y))
                    if box in selected:
                        self.assertEqual(local.count(),part.count(),(job['id'],box))
                        self.assertEqual(covered.overlap_area(part,(0,0)),0)
                        mask=pygame.image.tobytes(local.to_surface(setcolor=(255,255,255,255),unsetcolor=(0,0,0,0)),'RGBA')[3::4]
                        for index,on in enumerate(mask):
                            if on and actual[index*4:index*4+4]!=original[index*4:index*4+4]:
                                self.fail(f'Changed original pixel in {job["id"]} source{box}')
                        covered.draw(part,(0,0))
                    else:self.assertEqual(pygame.mask.from_surface(image,0).overlap_area(local,(0,0)),0)
                total+=1
            self.assertEqual(covered.count(),sum(p.count() for p in parts),job['id'])
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),record['sha256'])
        self.assertEqual(total,336)

    def test_facing_generation_references_are_exact_archived_originals(self):
        for job in self.jobs:
            source=ROOT/job['reference_file']
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),self.manifest[job['reference_file']]['sha256'])
            meta=json.loads((ROOT/f'paks/{job["pak"]}/pak.json').read_text())['authoring']
            self.assertEqual(meta['component_sources'][job['role']],job['file'])
            self.assertEqual(meta['component_grids'][job['role']],[job['columns'],job['rows']])


if __name__=='__main__':unittest.main()
