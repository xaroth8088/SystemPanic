"""Check procedural levels across seeds and render a reproducible layout gallery."""
import json
import math
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
from system_panic.app import App, autopilot
from system_panic.model import WIDTH, HEIGHT, circle_rect
from system_panic.paks import get_catalog
from system_panic.preferences import Preferences
from system_panic.world import World


def main():
    output = ROOT / "output/verification/levels"
    output.mkdir(parents=True, exist_ok=True)
    catalog = get_catalog()
    seeds, levels = (0, 3, 24, 101, 997), (1, 2, 7, 12, 50, 101)
    records, placed = [], 0
    for pak in catalog.paks:
        signatures = set()
        for seed in seeds:
            world = World(Preferences(), seed, solo=pak.id)
            for level in levels:
                world.enemies.clear()
                world.wave = level - 1
                world.start_wave()
                part = world.component("obstacles")
                before = world.rng.getstate()
                rebuilt = part.build(world)
                assert world.rng.getstate() == before, "Layout RNG must be separate from combat RNG"
                signature = tuple(tuple(c.rect) for c in world.cover)
                assert signature == tuple(tuple(c.rect) for c in rebuilt)
                signatures.add(signature)
                assert len(world.enemies) == level
                placed += len(world.enemies)
                for obstacle in world.cover:
                    rect = obstacle.rect
                    assert 0 < rect.left < rect.right < WIDTH and 0 < rect.top < rect.bottom < HEIGHT
                    assert obstacle.health == obstacle.max_health > 0
                for body in (world.player, *world.enemies):
                    assert not any(c.blocks_body(body) and c.overlaps_circle(body.pos, body.radius) for c in world.geometry)
                # Exercise advanced AI/attack patterns as well as factory stat queries.
                for _ in range(60):
                    world.advance(1 / 60, autopilot(world))
                assert all(math.isfinite(body.pos.x) and math.isfinite(body.pos.y) for body in (world.player, *world.enemies))
            world.close()
        assert len(signatures) == len(seeds) * len(levels)
        record = {"pak": pak.id, "seeds": list(seeds), "levels": list(levels), "unique_layouts": len(signatures)}
        records.append(record)
        print(json.dumps(record), flush=True)

    with tempfile.TemporaryDirectory(dir=output) as temporary:
        app = App(Path(temporary), 24, catalog)
        gallery = pygame.Surface((1440, len(catalog.complete_ids()) * 264))
        gallery.fill((9, 16, 25))
        font = pygame.font.Font(None, 23)
        for row, pak in enumerate(catalog.paks):
            app.start(pak.id)
            for column, level in enumerate((1, 2, 12)):
                world = app.world
                if level > 1:
                    world.enemies.clear()
                    world.wave = level - 1
                    world.start_wave()
                world.phase = "active"
                world.time = .1  # Select the visible frame of the pilot's arrival blink.
                before = (world.time, world.rng.getstate(), world.player.pos.copy())
                app.draw()
                assert before == (world.time, world.rng.getstate(), world.player.pos)
                pygame.image.save(app.canvas, output / f"{pak.id}-level-{level}.png")
                x, y = column * 480, row * 264
                gallery.blit(font.render(f"{pak.name} / LEVEL {level:02d}", True, pak.color), (x + 8, y + 3))
                gallery.blit(pygame.transform.scale(app.arena_surface, (480, 240)), (x, y + 24))
        pygame.image.save(gallery, output / "layout-gallery.png")
        app.quit()
        pygame.quit()
    report = {"procedural_cases": len(records) * len(seeds) * len(levels), "enemies_placed": placed,
              "separate_layout_rng": True, "geometry_and_spawn_safety": True,
              "advanced_ai_seconds_per_case": 1, "gallery_levels": [1, 2, 12], "paks": records}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{report['procedural_cases']} procedural cases; {placed} enemy placements; layout gallery saved.")


if __name__ == "__main__":
    main()
