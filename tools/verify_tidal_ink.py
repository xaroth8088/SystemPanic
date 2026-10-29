"""Inspect Tidal's actual jet/ink sequence in source or an external frozen observer."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
from time import perf_counter


def verify_tidal_ink(app, output):
    import pygame
    from system_panic.app import autopilot
    from system_panic.model import Controls, Vec
    from system_panic.preferences import Preferences
    from system_panic.world import World

    output.mkdir(parents=True, exist_ok=True)
    app.start("tidal_choir")
    w = app.world
    w.wave, w.phase, w.transition = 5, "active", 0.
    w.cover = []  # Isolate the actual attack for staged screenshots.
    w.player.pos, w.player.invulnerable = Vec(680, 300), 0.
    enemy = w.enemies[0]
    enemy.pos, enemy.vel = Vec(320, 240), Vec()
    enemy.state, enemy.timer, enemy.target = "windup", 0., Vec(680, 240)

    def screenshot(name):
        before = (w.time, w.rng.getstate(), w.player.pos.copy(), w.player.health, enemy.pos.copy(), enemy.vel.copy())
        app.toast_timer = 0
        app.draw()
        assert (w.time, w.rng.getstate(), w.player.pos, w.player.health, enemy.pos, enemy.vel) == before
        pygame.image.save(app.canvas, output / ("tidal-ink-" + name + ".png"))

    screenshot("windup")
    w.advance(1 / 60, Controls())
    hazards = importlib.import_module(type(w.component("enemy")).__module__ + ".hazards")
    cloud = next(p for p in w.projectiles if isinstance(p, hazards.Zone))
    origin = cloud.pos.copy()
    w.advance(.18, Controls())
    assert enemy.state == "charge" and cloud.age < cloud.delay
    screenshot("jet")
    surface = pygame.Surface((960, 480), pygame.SRCALPHA)
    cloud.draw(None, surface, w)
    assert surface.get_bounding_rect().width == 0
    for _ in range(27):
        w.advance(1 / 60, Controls())
    assert cloud.alive and cloud.age >= cloud.delay and cloud.pos == origin
    screenshot("active")
    cloud.draw(None, surface, w)
    assert pygame.mask.from_surface(surface, threshold=0).count() > 8000
    w.advance(.2, Controls())
    screenshot("drift")
    original_motion = app.prefs.reduced_motion, w.prefs.reduced_motion
    app.prefs.reduced_motion = True
    w.prefs.reduced_motion = True
    screenshot("reduced-motion")
    frames = []
    age = cloud.age
    for value in (cloud.delay, cloud.delay + cloud.duration * .9):
        cloud.age = value
        surface.fill((0, 0, 0, 0))
        cloud.draw(None, surface, w)
        frames.append(hashlib.sha256(pygame.image.tobytes(surface, "RGBA")).digest())
    assert frames[0] == frames[1]
    cloud.age = age
    app.prefs.reduced_motion, w.prefs.reduced_motion = original_motion
    health = w.player.health
    w.player.health = w.player.max_health * .1
    screenshot("low-hull")
    w.player.health = health
    for _ in range(40):
        w.advance(1 / 60, Controls())
    assert not cloud.alive
    screenshot("dissipated")

    timings = []
    cloud.alive, cloud.age = True, cloud.delay + .3
    for _ in range(200):
        start = perf_counter()
        surface.fill((0, 0, 0, 0))
        cloud.draw(None, surface, w)
        timings.append((perf_counter() - start) * 1000)

    runs = []
    for seed in (24, 73, 2026):
        world = World(Preferences(difficulty="relaxed"), seed, solo="tidal_choir", catalog=app.catalog)
        peak_ink = 0
        counts = {1: len(world.enemies)}
        try:
            for frame in range(180 * 60):
                world.advance(1 / 60, autopilot(world))
                world.drain_events()
                peak_ink = max(peak_ink, sum(type(p).__name__ == "Zone" for p in world.projectiles))
                if world.wave not in counts:
                    counts[world.wave] = len(world.enemies)
                    assert counts[world.wave] == world.wave
                if world.phase == "dead" or world.wave >= 8:
                    break
            record = dict(seed=seed, wave=world.wave, phase=world.phase, seconds=round(frame / 60, 2),
                          peak_ink=peak_ink, initial_enemy_counts=counts)
            runs.append(record)
            assert world.wave == 8 and world.phase == "active" and peak_ink > 0, record
        finally:
            world.close()
    return dict(hidden_until_active=True, filled_damage_area=True, charge_wake_rendered=True,
                render_preserves_simulation_and_rng=True, reduced_motion_steady=True,
                warm_draw_ms_mean=sum(timings) / len(timings), solo_samples=runs)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    from system_panic.app import App
    output = root / "output/verification/tidal-ink"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as directory:
        app = App(Path(directory), seed=24)
        try:
            report = verify_tidal_ink(app, output)
        finally:
            app.quit()
            pygame.quit()
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
