"""Export delivered Living Arcade originals into six independent role trees.

Development only. The source images are retained unchanged. Measured row bands
identify subjects; they never cut a connected subject at an artificial cell edge.
"""
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import pygame
from export_renewal import save_png, save_records, copy_audio

ROOT = Path(__file__).resolve().parents[2]
ROWS = {
    'canopy_capers': [0, 425, 720, 1018, 1254],
    'rime_rink': [0, 323, 640, 940, 1254],
    'storm_loom': [0, 352, 620, 874, 1254],
    'kiln_derby': [0, 320, 631, 930, 1254],
    'paper_pilgrimage': [0, 358, 641, 920, 1254],
    'ferric_ferry': [0, 327, 617, 895, 1254],
}
ROLES = ('pilot', 'enemy', 'weapon', 'obstacles')
FRINGE = 2


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def box_distance(first, second):
    """Distance between source bounds, then centers for unambiguous ties."""
    dx = max(0, first.left-second.right, second.left-first.right)
    dy = max(0, first.top-second.bottom, second.top-first.bottom)
    centers = (first.centerx-second.centerx)**2+(first.centery-second.centery)**2
    return dx*dx+dy*dy, centers


def extract_subjects(atlas, pak):
    """Return isolated lossless frames and explicit source/mask registration.

    Each delivered atlas has sixteen large, disconnected subjects and much
    smaller detached sparkle/glow islands. The clean measured size gap is
    validated rather than assuming an equal grid. Whole connected subjects can
    cross a nominal row or column boundary. Assign each extra substantial island
    to its nearest subject. Connected alpha-16 masks retain the visible glow;
    two further pixels preserve the original faint anti-aliased alpha fringe.
    A single ownership map prevents adjacent silhouettes leaking into a crop.
    Selected RGBA pixels are copied exactly, never resampled or recolored.
    """
    parts = pygame.mask.from_surface(atlas, 110).connected_components(160)
    parts.sort(key=lambda mask: mask.count(), reverse=True)
    if len(parts) < 16 or parts[15].count() < 10000:
        raise ValueError(f'Expected sixteen substantial delivered subjects: {pak}')
    if len(parts) > 16 and parts[16].count() >= parts[15].count()*.2:
        raise ValueError(f'No clean subject/glow size separation: {pak}')
    cores = parts[:16]
    core_boxes = [part.get_bounding_rects()[0] for part in cores]
    mapped = {}
    for index, box in enumerate(core_boxes):
        row = next((row for row, (top, bottom) in enumerate(zip(ROWS[pak], ROWS[pak][1:]))
                    if top <= box.centery < bottom), None)
        column = min(3, box.centerx*4//atlas.get_width())
        key = (row, column)
        if row is None or key in mapped:
            raise ValueError(f'Ambiguous measured source subject mapping: {pak}/{key}')
        mapped[key] = index
    if len(mapped) != 16:
        raise ValueError(f'Incomplete source subject mapping: {pak}')
    visible_parts = pygame.mask.from_surface(atlas, 16).connected_components(160)
    groups = [[] for _ in cores]
    for part in visible_parts:
        box = part.get_bounding_rects()[0]
        overlaps = [index for index, core in enumerate(cores) if part.overlap(core, (0, 0)) is not None]
        if len(overlaps) > 1:
            raise ValueError(f'Visible source glow connects sibling subjects: {pak}/{box}')
        nearest = overlaps[0] if overlaps else min(range(16), key=lambda index: box_distance(box, core_boxes[index]))
        groups[nearest].append(part)
    substantial_groups = [[] for _ in cores]
    for part in parts:
        parent = next(index for index, group in enumerate(groups)
                      if any(visible.overlap(part, (0, 0)) is not None for visible in group))
        substantial_groups[parent].append(part)
    owner = np.zeros(atlas.get_size(), dtype=np.uint8)
    for index, group in enumerate(groups):
        for part in group:
            box = part.get_bounding_rects()[0]
            # A small local bitmap keeps full-atlas mask-to-RGBA temporaries out
            # of the grouping loop while preserving each component's pixels.
            local = pygame.Mask(box.size)
            local.draw(part, (-box.left, -box.top))
            pixels = pygame.surfarray.array_alpha(local.to_surface(
                setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))) > 0
            view = owner[box.left:box.right, box.top:box.bottom]
            view[pixels] = index+1
    # Simultaneous discrete expansion assigns translucent edge/glow pixels to
    # exactly one original subject. Core labels never change during expansion.
    for _ in range(FRINGE):
        expanded = owner.copy()
        for dx, dy in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)):
            source_x = slice(max(0, -dx), min(atlas.get_width(), atlas.get_width()-dx))
            source_y = slice(max(0, -dy), min(atlas.get_height(), atlas.get_height()-dy))
            target_x = slice(max(0, dx), min(atlas.get_width(), atlas.get_width()+dx))
            target_y = slice(max(0, dy), min(atlas.get_height(), atlas.get_height()+dy))
            source, target = owner[source_x, source_y], expanded[target_x, target_y]
            fill = (target == 0) & (source > 0)
            target[fill] = source[fill]
        owner = expanded
    frames, metadata = {}, {}
    for row, role in enumerate(ROLES):
        images, records = [], []
        for column in range(4):
            index = mapped[(row, column)]
            boxes = [part.get_bounding_rects()[0] for part in groups[index]]
            bounds = boxes[0].unionall(boxes[1:]).inflate(FRINGE*2, FRINGE*2).clip(atlas.get_rect())
            image = atlas.subsurface(bounds).copy()
            excluded = owner[bounds.left:bounds.right, bounds.top:bounds.bottom] != index+1
            alpha = pygame.surfarray.pixels_alpha(image)
            alpha[excluded] = 0
            del alpha
            rgb = pygame.surfarray.pixels3d(image)
            rgb[excluded] = 0
            del rgb
            images.append(image)
            records.append(dict(source_bounds=list(bounds), core_bounds=list(core_boxes[index]),
                core_pixels=cores[index].count(),
                component_bounds=[list(part.get_bounding_rects()[0]) for part in substantial_groups[index]],
                substantial_pixels=sum(part.count() for part in substantial_groups[index]),
                visible_component_bounds=[list(box) for box in boxes],
                visible_pixels=sum(part.count() for part in groups[index]), fringe_pixels=FRINGE))
        tile = max(max(image.get_size()) for image in images)+8
        sheet = pygame.Surface((4*tile, tile), pygame.SRCALPHA)
        for column, (image, record) in enumerate(zip(images, records)):
            target = pygame.Rect(column*tile+(tile-image.get_width())//2,
                                 (tile-image.get_height())//2, *image.get_size())
            sheet.blit(image, target)
            record['destination_bounds'] = list(target)
        frames[role], metadata[role] = sheet, records
    return frames, metadata


def main():
    plan = json.loads(Path(__file__).with_name('living-prompts.json').read_text())
    prompts_path = Path(__file__).with_name('image-prompts.json')
    prompts = json.loads(prompts_path.read_text())
    records = []
    for job in plan['jobs']:
        pak = job['id']
        source = ROOT/job['file']
        atlas = pygame.image.load(source)
        if atlas.get_size() != (1254, 1254) or not atlas.get_flags() & pygame.SRCALPHA:
            raise ValueError('Unexpected delivered source geometry: '+str(source))
        frames, extraction = extract_subjects(atlas, pak)
        manifest_path = ROOT/f'paks/{pak}/pak.json'
        manifest = json.loads(manifest_path.read_text())
        overrides = manifest.get('authoring', {}).get('component_sources', {})
        for role in ROLES:
            if role in overrides:
                continue
            sheet = frames[role]
            target = ROOT/f'paks/{pak}/{role}/{role}_sheet.png'
            save_png(sheet, target)
            records.append(dict(file=target.relative_to(ROOT).as_posix(), source=job['file'],
                operation='Lossless whole-atlas connected-subject extraction; alpha-110/component-160 core identification, alpha-16/component-160 connected visible glow and nearest-core detached glows, exclusive 2px original-alpha fringe; four equal padded frames, no resampling',
                extraction=extraction[role], sha256=digest(target)))
        terrain = pygame.image.load(ROOT/f'paks/{pak}/obstacles/obstacles_sheet.png')
        icon = pygame.transform.smoothscale(terrain.subsurface((0, 0, terrain.get_height(), terrain.get_height())), (100, 100))
        background = pygame.Surface((960, 480), pygame.SRCALPHA)
        for row in range(5):
            for col in range(8):
                background.blit(icon, (col*150+(row%2)*65-30, row*125-25))
        target = ROOT/f'paks/{pak}/background/background_image.png'
        save_png(background, target)
        records.append(dict(file=target.relative_to(ROOT).as_posix(), source=job['file'],
            operation='Prepared decorative 960x480 mosaic from first registered terrain cell, resized to 100px', sha256=digest(target)))
        records.extend(copy_audio([job]))
        source_chime = ROOT/'assets/audio/production/pickup.ogg'
        target = ROOT/f'paks/{pak}/weapon/pickup.ogg'
        if not target.exists() or digest(target) != digest(source_chime):
            shutil.copyfile(source_chime, target)
        records.append(dict(file=target.relative_to(ROOT).as_posix(), source=source_chime.relative_to(ROOT).as_posix(), operation='Unmodified mastered original local Stable Audio 3 shared pickup chime', sha256=digest(target)))
        entry = dict(id=pak+'_living', file=job['file'], prompt=job['prompt'], transparent_background=True,
            actual_geometry=dict(columns=4, row_bands=list(zip(ROWS[pak], ROWS[pak][1:])), source_size=atlas.get_size(),
                                 row_bands_use='Subject identification hints only; connected silhouettes are never clipped to these bands.',
                                 extraction=extraction))
        prompts['jobs'] = [j for j in prompts['jobs'] if j['id'] != entry['id']]+[entry]
        manifest.setdefault('authoring', {}).update(animation_grid=[4,4], sheet_source=job['file'],
            source_row_edges=ROWS[pak])
        for role in ROLES:
            if role not in overrides:
                manifest['authoring'].setdefault('component_grids', {})[role]=[4,1]
        manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    prompts_path.write_text(json.dumps(prompts, indent=2)+'\n')
    save_records(records)
    print(f'Exported {len(records)} role-local original media files across six Paks.')


if __name__ == '__main__':
    main()
