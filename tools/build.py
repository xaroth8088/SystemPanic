"""Build the offline Windows x64 folder distribution with external Paks."""
import argparse
import json
from pathlib import Path
import os
import platform
import shutil
import struct

try:
    from .release_support import AUDIO_NAMES, build_metadata, release_paths, safe_remove_tree
except ImportError:  # Direct script execution.
    from release_support import AUDIO_NAMES, build_metadata, release_paths, safe_remove_tree

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Validate a clean tagged release before building")
    args = parser.parse_args()
    if os.name != "nt":
        raise SystemExit("This build command targets Windows; run play.py from source on other systems.")
    if struct.calcsize("P") != 8 or platform.machine().lower() not in ("amd64", "x86_64"):
        raise SystemExit("This distribution requires Windows x64 and a 64-bit x64 Python interpreter.")
    record = build_metadata(args.tag)
    paths = release_paths(record["version"])
    import PyInstaller.__main__
    paths["folder"].parent.mkdir(parents=True, exist_ok=True)
    # Check the absolute target before recursive cleanup. No old content enters a build.
    safe_remove_tree(paths["folder"], ROOT / "dist")
    PyInstaller.__main__.run([
        str(ROOT / "play.py"), "--name", "SystemPanic", "--onedir", "--windowed", "--noconfirm", "--clean",
        "--exclude-module", "numpy", "--exclude-module", "soundfile", "--exclude-module", "PIL",
        "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"), "--paths", str(ROOT / "src"),
        "--add-data", str(ROOT / "assets/images/title.png") + os.pathsep + "assets/images",
        *[argument for name in AUDIO_NAMES
          for argument in ("--add-data", str(ROOT / f"assets/audio/production/{name}.ogg") + os.pathsep + "assets/audio/production")],
        "--add-data", str(ROOT / "assets/manifest.json") + os.pathsep + "assets",
        "--add-data", str(ROOT / "LICENSE") + os.pathsep + ".",
    ])
    destination = paths["folder"] / "paks"
    destination.mkdir(exist_ok=True)
    for manifest in sorted((ROOT / "paks").glob("*/pak.json")):
        shutil.copytree(manifest.parent, destination / manifest.parent.name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copyfile(ROOT / "LICENSE", paths["folder"] / "LICENSE")
    (paths["folder"] / "BUILDINFO.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("Built:", ROOT / "dist/SystemPanic/SystemPanic.exe")


if __name__ == "__main__":
    main()
