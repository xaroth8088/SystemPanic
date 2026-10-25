"""Check mix stability and presentation pairs; optionally demand opening-level clears."""
import argparse
import itertools
import json
import math
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
from system_panic.app import App, autopilot
from system_panic.model import Vec
from system_panic.paks import discover, CHANNELS, GAMEPLAY_CHANNELS
from system_panic.preferences import Preferences
from system_panic.world import World


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pak-dir", type=Path, action="append", help="Explicit Pak roots instead of default locations")
    parser.add_argument("--case-file", type=Path, help="Replay mixes from a previous compatibility report's failures")
    parser.add_argument("--require-clear", action="store_true", help="Optional balance probe: fail if any tested mix cannot clear")
    parser.add_argument("--seconds", type=float, help="Active sample duration per mix (default 1s, or 60s with --require-clear)")
    args = parser.parse_args()
    seconds = args.seconds if args.seconds is not None else (60 if args.require_clear else 1)
    if not math.isfinite(seconds) or seconds <= 0:
        parser.error("--seconds must be finite and positive")
    catalog = discover(args.pak_dir)
    if catalog.missing(catalog.by_id):
        parser.error("The installed mix does not cover all six component channels")
    failures = []
    completed = 0
    maximum = 0
    pools = [catalog.providers(channel) for channel in GAMEPLAY_CHANNELS]
    total = math.prod(map(len, pools))
    combinations = itertools.product(*pools)
    if args.case_file:
        previous = json.loads(args.case_file.read_text(encoding="utf-8"))
        combinations = [tuple(case["mix"][channel] for channel in GAMEPLAY_CHANNELS) for case in previous["failures"]]
        total = len(combinations)
    for index, combo in enumerate(combinations, 1):
        world = World(Preferences(difficulty="relaxed", shuffle_channels=[], enabled=list(catalog.by_id)), seed=24, catalog=catalog)
        world.mix.update(zip(GAMEPLAY_CHANNELS, combo))
        world.cover = world.component("obstacles").build(world)
        world.player.pos = world.safe_position(Vec(480, 240), 13)
        world.enemies.clear()
        world.wave = 0
        world.start_wave()
        world.phase = "active"  # Sample gameplay, not the initial introduction.
        for frame in range(max(1, math.ceil(seconds * 60))):
            world.advance(1 / 60, autopilot(world))
            world.drain_events()
            bodies = (world.player, *world.enemies)
            if not all(math.isfinite(value) for body in bodies for value in (body.pos.x, body.pos.y, body.health)):
                failures.append({"mix":world.mix.copy(),"reason":"nonfinite body state"})
                break
            if world.wave > 1 or world.phase == "dead":
                break
        maximum = max(maximum, frame / 60)
        if world.wave > 1:
            completed += 1
        elif args.require_clear:
            failures.append({"mix":world.mix, "phase":world.phase, "health":world.player.health,
                             "remaining":len(world.enemies), "kills":world.kills})
        world.close()
        if index % 216 == 0:
            print(f"{index}/{total} checked; {len(failures)} failures", flush=True)
    output = ROOT / ("output/verification/compatibility-replay.json" if args.case_file else "output/verification/compatibility.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    pairs = 0
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        app = App(Path(temporary), 24, catalog)
        app.start()
        for background, music in itertools.product(catalog.providers("background"), catalog.providers("music")):
            app.world.mix.update(background=background, music=music)
            app.world.component("background")
            track = app.world.component("music").track(app.world)
            app.audio.music(track)
            before = (app.world.time, app.world.player.pos.copy(), app.world.rng.getstate())
            app.draw()
            assert before == (app.world.time, app.world.player.pos, app.world.rng.getstate()), "Presentation must not advance gameplay"
            assert app.audio.current == (track.path if track else None)
            pairs += 1
        app.quit()
        pygame.quit()
    report = {"combinations":total, "opening_wave_cleared":completed, "difficulty":"relaxed",
              "mode":"require_clear" if args.require_clear else "stability", "seconds_per_mix":seconds,
              "presentation_pairs_checked":pairs, "full_mix_space":math.prod(len(catalog.providers(c)) for c in CHANNELS),
              "seed":24, "max_seconds":maximum, "failures":failures}
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "failures"}), flush=True)
    if failures:
        raise SystemExit("Some combinations failed the requested check; see compatibility report")


if __name__ == "__main__":
    main()
