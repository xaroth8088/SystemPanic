"""Render performance recovery/management and probe real wall-clock frame timing."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame
from system_panic.app import App
from system_panic.combinations import CombinationHistory, mix_key
from system_panic.model import Controls
from system_panic.paks import CHANNELS


def verify_combinations(app, output):
    def screenshot(name):
        app.toast_timer = 0
        app.draw()
        pygame.image.save(app.canvas, output / ("combinations-" + name + ".png"))

    def detect():
        context = app.performance_context()
        for _ in range(5):
            app.check_performance(.25, context)
        assert app.route == "performance"

    app.home()
    app.start()
    world = app.world
    world.phase = "active"
    world.score, world.kills, world.powerups_collected = 1234, 8, 2
    mix = world.mix.copy()
    before = (world.time, world.player.pos.copy(), world.wave, world.rng.getstate())
    detect()
    app.update(5, Controls(fire=True))
    assert (world.time, world.player.pos, world.wave, world.rng.getstate()) == before
    assert mix_key(mix) in CombinationHistory(app.store.path.parent).keys
    screenshot("normal-dialog")
    app.dismiss_performance()
    assert app.route == "game" and app.world is world and world.mix != mix
    assert (world.score, world.kills, world.powerups_collected) == (1234, 8, 2)
    assert world.transition == 0
    screenshot("recovered-game")
    recovered = world.mix.copy()
    app.home()
    app.start(fixed_mix=recovered)
    app.world.phase = "active"
    detect()
    screenshot("remix-dialog")
    app.dismiss_performance()
    assert app.route == "home" and app.world is None
    app.open_page("settings")
    screenshot("settings")
    app.open_page("combinations")
    screenshot("history")
    selected = app.selected_flagged()
    app.remove_flagged()
    assert mix_key(selected.mix) not in CombinationHistory(app.store.path.parent).keys
    screenshot("reenabled")
    app.home()
    solo = next(p for p in app.catalog.complete_ids()
                if mix_key(dict.fromkeys(CHANNELS, p)) not in app.combination_history.keys)
    app.start(solo)
    app.world.phase = "active"
    original_path = app.combination_history.path
    try:
        # A file cannot replace its containing directory; no original bytes change.
        app.combination_history.path = original_path.parent
        detect()
    finally:
        app.combination_history.path = original_path
    assert app.combination_history.dirty
    screenshot("disk-error")
    assert app.combination_history.retry()
    app.dismiss_performance()
    assert app.route == "home"
    for entry in list(app.combination_history.entries):
        assert app.combination_history.remove(mix_key(entry.mix))
    app.open_page("combinations")
    screenshot("empty")
    app.home()
    return {"exact_normal_mix": mix, "recovery_mix": recovered, "normal_progress_retained": True,
            "static_remix_returns_home": True, "solo_returns_home": True, "remove_persists": True,
            "disk_failure_excluded_in_memory_and_retried": True, "paused_world_unchanged": True,
            "synthetic_dialog_probe": {"fps": 4, "seconds": 1.25}}


def main():
    output = ROOT / "output/verification/combinations"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        app = App(Path(temporary), seed=24)
        report = verify_combinations(app, output)
        # Inject a slow presentation into the real tick/update/draw loop. Simulation
        # remains ordinary; this verifies elapsed time is not the .25s simulation cap.
        safe_solo = next(p for p in app.catalog.complete_ids()
                         if mix_key(dict.fromkeys(CHANNELS, p)) not in app.combination_history.keys)
        app.start(safe_solo)
        app.world.phase = "active"
        app.world.player.invulnerable = 100
        draw = app.draw
        started = time.perf_counter()
        def slow_draw():
            draw()
            if app.route == "game":
                time.sleep(.125)
            elif app.route == "performance":
                pygame.image.save(app.canvas, output / "combinations-real-slow-frame.png")
                app.running = False
            if time.perf_counter() - started > 10:
                raise AssertionError("Wall-clock watchdog did not interrupt")
        app.draw = slow_draw
        try:
            app.run()
        finally:
            app.draw = draw
        assert app.route == "performance"
        _, fps, seconds = app.performance_problem
        assert fps < 10 and seconds > 1
        assert mix_key(app.performance_problem[0]) in CombinationHistory(Path(temporary)).keys
        report["real_wall_clock_probe"] = {"fps": fps, "slow_seconds": seconds,
                                           "injected_presentation_delay": .125, "paused": True}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
