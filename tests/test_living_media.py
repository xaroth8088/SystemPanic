"""Whole-source sprite conservation and media checks using runtime dependencies."""
from array import array
import hashlib
import json
import os
from pathlib import Path
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame

ROOT = Path(__file__).resolve().parents[1]
PAKS = ('canopy_capers', 'rime_rink', 'storm_loom', 'kiln_derby', 'paper_pilgrimage', 'ferric_ferry')
ROLES = ('pilot', 'enemy', 'weapon', 'obstacles')


def original_sheet(pak,role):
    metadata=json.loads((ROOT/f'paks/{pak}/pak.json').read_text())
    return metadata.get('authoring',{}).get('component_snapshots',{}).get(role,f'paks/{pak}/{role}/{role}_sheet.png')


def local_mask(mask, bounds):
    result = pygame.Mask(bounds.size)
    result.draw(mask, (-bounds.left, -bounds.top))
    return result


class LivingMediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = {record['file']: record for record in json.loads((ROOT/'assets/manifest.json').read_text())['assets']}

    def test_all_96_whole_subjects_and_visible_glows_survive_exactly_once(self):
        subjects = 0
        for pak in PAKS:
            with self.subTest(pak=pak):
                atlas = pygame.image.load(ROOT/f'assets/images/{pak}-source.png')
                # Lower-alpha connected masks include visible original glows;
                # these are stricter than the alpha-110 core-subject guarantee.
                parts = pygame.mask.from_surface(atlas, 16).connected_components(160)
                by_bounds = {tuple(part.get_bounding_rects()[0]): part for part in parts}
                covered = pygame.Mask(atlas.get_size())
                for role in ROLES:
                    path = original_sheet(pak,role)
                    sheet = pygame.image.load(ROOT/path)
                    for record in self.manifest[path]['extraction']:
                        subjects += 1
                        bounds = pygame.Rect(record['source_bounds'])
                        image = sheet.subsurface(pygame.Rect(record['destination_bounds']))
                        output = pygame.image.tobytes(image, 'RGBA')
                        source = pygame.image.tobytes(atlas.subsurface(bounds), 'RGBA')
                        output_mask = pygame.mask.from_surface(image, 0)
                        assigned = {tuple(box) for box in record['visible_component_bounds']}
                        for box, part in by_bounds.items():
                            if not bounds.colliderect(pygame.Rect(box)):
                                continue
                            pixels = local_mask(part, bounds)
                            if box in assigned:
                                self.assertEqual(pixels.count(), part.count(), (pak, role, 'clipped subject', box))
                                self.assertEqual(covered.overlap_area(part, (0, 0)), 0, (pak, role, 'duplicate subject', box))
                                mask_bytes = pygame.image.tobytes(pixels.to_surface(
                                    setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)), 'RGBA')[3::4]
                                for index, selected in enumerate(mask_bytes):
                                    if selected:
                                        offset = index*4
                                        if output[offset:offset+4] != source[offset:offset+4]:
                                            self.fail(f'Changed source RGBA pixel: {pak}/{role} source box {box}, pixel {index}')
                                covered.draw(part, (0, 0))
                            else:
                                self.assertEqual(output_mask.overlap_area(pixels, (0, 0)), 0,
                                                 (pak, role, 'sibling leaked', box))
                self.assertEqual(covered.count(), sum(part.count() for part in parts), pak)
        self.assertEqual(subjects, 96)

    def test_registered_exports_keep_original_hashes_and_explicit_source_bounds(self):
        for pak in PAKS:
            source = f'assets/images/{pak}-source.png'
            self.assertEqual(hashlib.sha256((ROOT/source).read_bytes()).hexdigest(), self.manifest[source]['sha256'])
            for role in ROLES:
                path = original_sheet(pak,role)
                sheet = pygame.image.load(ROOT/path)
                self.assertEqual(sheet.get_width(), sheet.get_height()*4, path)
                records = self.manifest[path]['extraction']
                self.assertEqual(len(records), 4, path)
                for record in records:
                    self.assertTrue(pygame.Rect(record['source_bounds']).contains(pygame.Rect(record['core_bounds'])), path)
                    self.assertGreater(record['core_pixels'], 10000, path)
                self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), self.manifest[path]['sha256'])

    def test_overlapping_measured_rows_preserve_the_full_antenna_and_harpoon(self):
        paper = self.manifest[original_sheet('paper_pilgrimage','enemy')]['extraction'][0]
        self.assertLess(paper['core_bounds'][1], 358)
        self.assertLessEqual(paper['source_bounds'][1], paper['core_bounds'][1])
        storm = self.manifest['paks/storm_loom/weapon/weapon_sheet.png']['extraction'][2]
        core = pygame.Rect(storm['core_bounds'])
        self.assertGreater(core.bottom, 874)
        self.assertGreaterEqual(pygame.Rect(storm['source_bounds']).bottom, core.bottom)

    def test_new_audio_copies_match_original_masters_and_decode(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
        try:
            unique = set()
            for pak in PAKS:
                for role, filename, stem in (('music', 'music.ogg', pak), ('pilot', 'special.ogg', pak+'_special'),
                                             ('weapon', 'shot.ogg', pak+'_shot'), ('weapon', 'pickup.ogg', 'pickup')):
                    target = ROOT/f'paks/{pak}/{role}/{filename}'
                    source = ROOT/f'assets/audio/production/{stem}.ogg'
                    self.assertEqual(target.read_bytes(), source.read_bytes(), str(target))
                    sound = pygame.mixer.Sound(target)
                    self.assertGreater(sound.get_length(), .04, stem)
                    pcm = array('h', sound.get_raw())
                    self.assertGreater(max(abs(value) for value in pcm), 300, stem)
                    if stem != 'pickup':
                        unique.add(hashlib.sha256(target.read_bytes()).hexdigest())
            self.assertEqual(len(unique), 18)
        finally:
            pygame.mixer.quit()


if __name__ == '__main__':
    unittest.main()
