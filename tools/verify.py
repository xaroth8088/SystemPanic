"""Reproducible full-run simulations, local asset checks, and UI screenshots."""
from __future__ import annotations
import argparse
import hashlib
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
from system_panic.app import App, autopilot
from system_panic.paks import PAKS
from system_panic.preferences import Preferences
from system_panic.world import World


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/verification")
    parser.add_argument("--seconds", type=int, default=300)
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    report = {"runtime":sys.version, "pygame":pygame.version.ver, "runs":[], "assets":[]}
    for pak in PAKS:
        world = World(Preferences(difficulty="relaxed"), 24, solo=pak.id)
        for frame in range(args.seconds * 60):
            world.advance(1 / 60, autopilot(world))
            world.drain_events()
            if world.phase in ("dead", "victory"):
                break
        record = {"pak":pak.id, "phase":world.phase, "wave":world.wave, "kills":world.kills,
                  "health":round(world.player.health, 2), "score":world.score, "seconds":round(frame / 60, 2)}
        report["runs"].append(record)
        print(json.dumps(record), flush=True)
    with tempfile.TemporaryDirectory(dir=output) as temp:
        app = App(Path(temp), 24)
        for screen in ("home", "settings", "help", "credits"):
            app.route = screen
            app.draw()
            pygame.image.save(app.canvas, output / (screen + ".png"))
        for pak in PAKS:
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
        app.world.phase = "victory"
        app.route = "outcome"
        app.draw()
        pygame.image.save(app.canvas, output / "victory.png")
        pygame.quit()
    for path in sorted((ROOT / "assets").rglob("*")):
        if path.is_file() and path.suffix in (".ogg", ".png"):
            report["assets"].append({"file":str(path.relative_to(ROOT)).replace("\\", "/"),
                                     "bytes":path.stat().st_size, "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    if not all(run["phase"] == "victory" for run in report["runs"]):
        raise SystemExit("At least one full solo run did not finish; inspect report.json")
    print("Six complete solo victories; screenshots and asset hashes saved.")


if __name__ == "__main__":
    main()
