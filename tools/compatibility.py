"""Play a full opening wave in every one of the 6^4 component mixtures."""
import argparse
import itertools
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
from system_panic.app import autopilot
from system_panic.model import Vec
from system_panic.paks import discover, CHANNELS
from system_panic.preferences import Preferences
from system_panic.world import World


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pak-dir", type=Path, action="append", help="Explicit Pak roots instead of default locations")
    args = parser.parse_args()
    catalog = discover(args.pak_dir)
    if catalog.missing(catalog.by_id):
        parser.error("The installed mix does not cover all four component channels")
    failures = []
    completed = 0
    maximum = 0
    pools = [catalog.providers(channel) for channel in CHANNELS]
    total = math.prod(map(len, pools))
    for index, combo in enumerate(itertools.product(*pools), 1):
        world = World(Preferences(difficulty="relaxed", shuffle_channels=[], enabled=list(catalog.by_id)), seed=24, catalog=catalog)
        world.mix = dict(zip(CHANNELS, combo))
        world.cover = world.pak("arena").make_arena()
        world.player.pos = world.safe_position(Vec(480, 240), 13)
        world.enemies.clear()
        world.wave = 0
        world.start_wave()
        for frame in range(60 * 60):
            world.advance(1 / 60, autopilot(world))
            world.drain_events()
            if world.wave > 1 or world.phase == "dead":
                break
        maximum = max(maximum, frame / 60)
        if world.wave > 1:
            completed += 1
        else:
            failures.append({"mix":world.mix, "phase":world.phase, "health":world.player.health,
                             "remaining":len(world.enemies), "kills":world.kills})
        if index % 216 == 0:
            print(f"{index}/{total} checked; {len(failures)} failures", flush=True)
    report = {"combinations":total, "opening_wave_cleared":completed, "difficulty":"relaxed",
              "seed":24, "max_seconds":maximum, "failures":failures}
    output = ROOT / "output/verification/compatibility.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "failures"}), flush=True)
    if failures:
        raise SystemExit("Some combinations stalled or died; see compatibility.json")


if __name__ == "__main__":
    main()
