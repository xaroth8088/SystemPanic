"""Play a full opening wave in every one of the 6^4 component mixtures."""
import itertools
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
from system_panic.app import autopilot
from system_panic.model import Vec
from system_panic.paks import PAKS, CHANNELS
from system_panic.preferences import Preferences
from system_panic.world import World


def main():
    failures = []
    completed = 0
    maximum = 0
    for index, combo in enumerate(itertools.product(PAKS, repeat=4), 1):
        world = World(Preferences(difficulty="relaxed", shuffle_channels=[]), seed=24)
        world.mix = dict(zip(CHANNELS, (p.id for p in combo)))
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
            print(f"{index}/1296 checked; {len(failures)} failures", flush=True)
    report = {"combinations":1296, "opening_wave_cleared":completed, "difficulty":"relaxed",
              "seed":24, "max_seconds":maximum, "failures":failures}
    output = ROOT / "output/verification/compatibility.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "failures"}), flush=True)
    if failures:
        raise SystemExit("Some combinations stalled or died; see compatibility.json")


if __name__ == "__main__":
    main()
