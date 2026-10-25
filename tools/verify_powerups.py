"""Run every Pak's collectible checks in source and optionally the Windows build."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
import pygame
from system_panic.app import App
from powerup_probe import exercise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", action="store_true")
    args = parser.parse_args()
    output = ROOT / "output/verification/powerups-integration"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        app = App(Path(temporary), 24)
        try:
            report = exercise(app, output / "source")
        finally:
            app.quit()
            pygame.quit()
        (output / "source.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Source: all twelve tenth-kill drops, pickups, rendering and retained upgrades passed.", flush=True)
    if args.frozen:
        with tempfile.TemporaryDirectory(dir=output) as temporary:
            temporary = Path(temporary)
            shutil.copytree(ROOT / "paks", temporary / "paks", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            pilot = temporary / "paks/signal_runner/pilot"
            shutil.copyfile(ROOT / "tools/powerup_probe.py", pilot / "_powerup_probe.py")
            hook = f'''
from ._powerup_probe import exercise
from system_panic.app import App
from pathlib import Path
import json
import traceback
import pygame

def _verify_powerups(self, *args, **kwargs):
    try:
        report = exercise(self, Path({str(output / "frozen")!r}))
        Path({str(output / "frozen.json")!r}).write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception:
        Path({str(output / "frozen-error.log")!r}).write_text(traceback.format_exc(), encoding="utf-8")
        raise SystemExit(1)
    finally:
        self.quit()
        pygame.quit()
App.run = _verify_powerups
'''
            entry = pilot / "pilot.py"
            entry.write_text(entry.read_text(encoding="utf-8") + hook, encoding="utf-8")
            result = subprocess.run([str(ROOT / "dist/SystemPanic/SystemPanic.exe"), "--headless", "--pak-dir", str(temporary / "paks"),
                                     "--data-dir", str(temporary / "profile"), "--frames", "1"],
                                    cwd=temporary, capture_output=True, timeout=120)
            if result.returncode:
                error = output / "frozen-error.log"
                raise AssertionError(error.read_text(encoding="utf-8") if error.exists() else result.stderr.decode(errors="replace"))
            report = json.loads((output / "frozen.json").read_text(encoding="utf-8"))
            assert report["all_paks"] == 12
        print("Frozen: all twelve collectible and upgrade-persistence checks passed.", flush=True)


if __name__ == "__main__":
    main()
