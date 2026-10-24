"""Export the original AI atlas/music into self-contained launch Pak assets."""
import hashlib
import json
import os
from pathlib import Path
import shutil

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

ROOT = Path(__file__).resolve().parents[2]
ROWS = ((0, 310), (310, 565), (565, 805), (805, 1024))
TARGETS = ("pilot/pilot_sheet.png", "enemy/enemy_sheet.png", "obstacles/obstacles_sheet.png", "weapon/weapon_sheet.png")


def main():
    source = ROOT / "assets/images/sprites-source.png"
    atlas = pygame.image.load(source)
    width = atlas.get_width() // 6
    records = []
    for manifest in sorted((ROOT / "paks").glob("*/pak.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        column = data.get("authoring", {}).get("atlas_column")
        if column is None:
            continue
        directory = manifest.parent
        for row, relative in enumerate(TARGETS):
            target = directory / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            top, bottom = ROWS[row]
            crop = atlas.subsurface((column * width + 14, top, width - 28, bottom - top))
            bounds = crop.get_bounding_rect(min_alpha=140)
            if bounds.width and bounds.height:
                crop = crop.subsurface(bounds)
            pygame.image.save(crop, target)
            records.append({"file":target.relative_to(ROOT).as_posix(), "source":source.relative_to(ROOT).as_posix(),
                            "operation":f"Lossless atlas crop, column {column}, row {row}; trim transparent bounds", "sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
        background = directory / "background/background_image.png"
        background.parent.mkdir(exist_ok=True)
        title = ROOT / "assets/images/title.png"
        pygame.image.save(pygame.transform.smoothscale(pygame.image.load(title), (960, 480)), background)
        records.append({"file":background.relative_to(ROOT).as_posix(), "source":title.relative_to(ROOT).as_posix(),
                        "operation":"Resized original AI title to 960x480 for component-local scenery", "sha256":hashlib.sha256(background.read_bytes()).hexdigest()})
        for original, relative in ((data['id'], "music/music.ogg"), ("select", "pilot/special.ogg"), ("shot", "weapon/shot.ogg")):
            source_audio = ROOT / f"assets/audio/production/{original}.ogg"
            target = directory / relative
            shutil.copyfile(source_audio, target)
            records.append({"file":target.relative_to(ROOT).as_posix(), "source":source_audio.relative_to(ROOT).as_posix(),
                            "operation":"Unmodified copy into component folder", "sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
    (ROOT / "assets/pak-exports.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(records)} original Pak assets")


if __name__ == "__main__":
    main()
