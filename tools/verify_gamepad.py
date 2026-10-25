"""Drive source and optional frozen builds using a native SDL virtual controller."""
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
os.environ.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1",
                  SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS="1")

import pygame
from system_panic.app import App
from gamepad_probe import exercise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", action="store_true", help="Also exercise the current Windows executable with a drop-in QA helper")
    args = parser.parse_args()
    output = ROOT / "output/verification/gamepad"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as directory:
        app = App(Path(directory), 24)
        try:
            report = exercise(app, output / "source")
        finally:
            app.quit()
            pygame.quit()
        (output / "source.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Source: native controller UI, all solo games, disconnect/reconnect and focus checks passed.", flush=True)
    if args.frozen:
        with tempfile.TemporaryDirectory(dir=output) as directory:
            temporary = Path(directory)
            shutil.copytree(ROOT / "paks", temporary / "paks", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            pilot = temporary / "paks/signal_runner/pilot"
            shutil.copyfile(ROOT / "tools/gamepad_probe.py", pilot / "_gamepad_probe.py")
            destination = str(output / "frozen")
            hook = f'''
from ._gamepad_probe import exercise
from system_panic.app import App
from pathlib import Path
import json
import pygame
import traceback
def _verify_input(self, *args, **kwargs):
    try:
        result = exercise(self, Path({destination!r}))
        Path({str(output / 'frozen.json')!r}).write_text(json.dumps(result, indent=2), encoding="utf-8")
    except Exception:
        Path({str(output / 'frozen-error.log')!r}).write_text(traceback.format_exc(), encoding="utf-8")
        raise SystemExit(1)
    finally:
        self.quit()
        pygame.quit()
App.run = _verify_input
'''
            entry = pilot / "pilot.py"
            entry.write_text(entry.read_text(encoding="utf-8") + hook, encoding="utf-8")
            result = subprocess.run([str(ROOT / "dist/SystemPanic/SystemPanic.exe"), "--headless", "--pak-dir", str(temporary / "paks"),
                                     "--data-dir", str(temporary / "profile"), "--seed", "24", "--frames", "1"],
                                    cwd=temporary, capture_output=True, timeout=120)
            if result.returncode:
                error_file = output / "frozen-error.log"
                raise AssertionError((result.returncode, error_file.read_text(encoding="utf-8") if error_file.exists() else result.stderr.decode(errors="replace")))
            report = json.loads((output / "frozen.json").read_text(encoding="utf-8"))
            assert report["native_sdl_virtual_controller"] and len(report["solo_inputs"]) == len(app.catalog.complete_ids())
        print("Frozen: same native controller checks passed through the packaged SDL backend.", flush=True)


if __name__ == "__main__":
    main()
