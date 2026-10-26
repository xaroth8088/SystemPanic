"""Bounded samples of endless runs, local asset checks, and UI screenshots."""
from __future__ import annotations
import argparse
import hashlib
import json
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
from system_panic.model import Controls
from system_panic.paks import CHANNELS, discover
from system_panic.preferences import Preferences
from system_panic.world import World


def verify_static_remix(app, output):
    """Exercise saved choices and static scheduling without imposing mixed-Pak balance."""
    def screenshot(name):
        app.toast_timer = 0
        app.draw()
        pygame.image.save(app.canvas, output / ("static-remix-" + name + ".png"))

    # The main run is still paused here. Saving must capture exactly its live mix.
    world = app.world
    live_mix = world.mix.copy()
    before = (world.time, world.player.pos.copy(), world.rng.getstate(), world.wave)
    app.name_remix(from_run=True)
    app.remix_name = "Saved from the main game"
    screenshot("pause-save")
    app.update(2, Controls(fire=True))
    app.save_remix_name()
    assert app.route == "pause"
    assert (world.time, world.player.pos, world.rng.getstate(), world.wave) == before
    assert app.remix_store.load()[-1].mix == live_mix
    assert world.fixed_mix is None, "Saving a live mix cannot change the main game mode"
    main_can_shuffle = world.can_shuffle
    if main_can_shuffle:
        previous_count = world.shuffle_count
        world.shuffle()
        assert world.shuffle_count == previous_count + 1 and world.mix != live_mix
        assert app.remix_store.load()[-1].mix == live_mix

    app.home()
    app.open_remix()
    selected = {channel: providers[index % len(providers)]
                for index, channel in enumerate(CHANNELS)
                if (providers := app.catalog.providers(channel))}
    app.remix_mix = selected.copy()
    screenshot("builder")
    app.pick_remix_channel("pilot")
    screenshot("providers")
    app.choose_remix_provider(selected["pilot"])
    app.name_remix()
    app.remix_name = "After Hours"
    screenshot("name")
    app.save_remix_name()
    favorite = app.selected_remix()
    assert favorite is not None and favorite.mix == selected
    identifier = favorite.id
    app.name_remix(rename=True)
    app.remix_name = "After Hours Arcade"
    app.save_remix_name()
    assert app.selected_remix().id == identifier
    assert app.selected_remix().name == "After Hours Arcade"
    screenshot("favorite")
    app.open_page("remix-saved")
    screenshot("saved")
    app.load_remix(identifier)
    app.open_page("remix-delete")
    screenshot("delete")
    app.back()
    assert any(item.id == identifier for item in app.remixes)

    app.play_remix()
    world = app.world
    assert world.fixed_mix == selected and world.mix == selected
    assert not world.can_shuffle
    before = (world.rng.getstate(), world.player.pos.copy(), world.shuffle_timer,
              world.projectiles.copy(), world.events.copy())
    world.shuffle()
    assert (world.rng.getstate(), world.player.pos, world.shuffle_timer,
            world.projectiles, world.events) == before
    # An expired timer must not trigger a provider change, even with shuffle preferences on.
    world.shuffle_timer = -1
    for _ in range(240):
        app.update(1 / 60, autopilot(world))
    assert world.mix == selected and world.shuffle_count == 0 and world.transition == 0
    assert world.time > 0
    screenshot("gameplay")
    record = {"mix": selected, "manual_shuffle_unchanged": True,
              "expired_timer_unchanged": True, "shuffle_count": world.shuffle_count,
              "active_seconds": round(world.time, 3), "phase": world.phase,
              "live_mix_saved_without_advancing_run": True,
              "main_game_can_still_shuffle": main_can_shuffle,
              "favorite_save_rename_load": True}

    app.home()
    app.open_remix()
    app.open_page("remix-saved")
    app.load_remix(identifier)
    app.open_page("remix-delete")
    app.delete_remix()
    assert all(item.id != identifier for item in app.remix_store.load())
    record["favorite_delete"] = True
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/verification")
    parser.add_argument("--seconds", type=int, default=300)
    parser.add_argument("--levels", type=int, default=12, help="Levels to clear per Pak before stopping the QA sample")
    parser.add_argument("--pak-dir", type=Path, action="append", help="Explicit Pak roots instead of default locations")
    args = parser.parse_args()
    if args.levels < 1 or args.seconds <= 0:
        parser.error("--levels and --seconds must be positive")
    catalog = discover(args.pak_dir)
    if catalog.missing(catalog.by_id):
        parser.error("The installed mix does not cover all six component channels")
    paks = tuple(p for p in catalog.paks if p.complete)
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    report = {"runtime":sys.version, "pygame":pygame.version.ver, "progression":"endless_plus_one",
              "target_levels":args.levels, "runs":[], "assets":[]}
    for pak in paks:
        world = World(Preferences(difficulty="relaxed", enabled=list(catalog.by_id)), 24, solo=pak.id, catalog=catalog)
        start_counts = {world.wave:len(world.enemies)}
        for frame in range(args.seconds * 60):
            world.advance(1 / 60, autopilot(world))
            world.drain_events()
            if world.wave not in start_counts:
                start_counts[world.wave] = len(world.enemies)
                assert len(world.enemies) == world.wave, "Enemy count must grow by exactly one per level"
            if world.phase == "dead" or world.wave > args.levels:
                break
        record = {"pak":pak.id, "phase":world.phase, "wave":world.wave, "kills":world.kills,
                  "cleared_levels":world.wave - 1 + int(world.phase == "clear"),
                  "initial_enemies_per_level":start_counts,
                  "health":round(world.player.health, 2), "score":world.score, "seconds":round(frame / 60, 2)}
        report["runs"].append(record)
        print(json.dumps(record), flush=True)
    with tempfile.TemporaryDirectory(dir=output) as temp:
        app = App(Path(temp), 24, catalog)
        for screen in ("home", "settings", "controls", "help", "credits", "paks"):
            app.route = screen
            app.draw()
            pygame.image.save(app.canvas, output / (screen + ".png"))
        for pak in paks:
            app.start(pak.id)
            for _ in range(480):
                app.update(1 / 60, autopilot(app.world))
            app.draw()
            pygame.image.save(app.canvas, output / (pak.id + ".png"))
        app.start()
        app.world.shuffle()
        app.draw()
        pygame.image.save(app.canvas, output / "remix.png")
        app.route = "pause"
        app.draw()
        pygame.image.save(app.canvas, output / "pause.png")
        report["static_remix"] = verify_static_remix(app, output)
        # Preserve the original main-mode defeat render after the static checks.
        app.start()
        app.world.player.health = 0
        app.world.phase = "dead"
        app.route = "outcome"
        app.draw()
        pygame.image.save(app.canvas, output / "game-over.png")
        app.quit()
        pygame.quit()
    for path in sorted([*(ROOT / "assets").rglob("*"), *(ROOT / "paks").rglob("*")]):
        if path.is_file() and path.suffix in (".ogg", ".png"):
            report["assets"].append({"file":str(path.relative_to(ROOT)).replace("\\", "/"),
                                     "bytes":path.stat().st_size, "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    if not all(run["cleared_levels"] >= args.levels and run["phase"] == "active" for run in report["runs"]):
        raise SystemExit(f"At least one solo sample did not clear {args.levels} levels; inspect report.json")
    print(f"All {len(paks)} complete Paks cleared {args.levels} levels and continued playing; screenshots and hashes saved.")


if __name__ == "__main__":
    main()
