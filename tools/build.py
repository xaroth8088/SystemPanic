"""Build the offline Windows folder distribution with only production assets."""
from pathlib import Path
import os
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    if os.name != "nt":
        raise SystemExit("This build command targets Windows; run play.py from source on other systems.")
    import PyInstaller.__main__
    PyInstaller.__main__.run([
        str(ROOT / "play.py"), "--name", "SystemPanic", "--onedir", "--windowed", "--noconfirm", "--clean",
        "--exclude-module", "numpy", "--exclude-module", "soundfile", "--exclude-module", "PIL",
        "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"), "--paths", str(ROOT / "src"),
        "--add-data", str(ROOT / "assets/images/title.png") + os.pathsep + "assets/images",
        *[argument for name in ("shot", "impact", "shuffle", "hurt", "clear", "select", "game_over")
          for argument in ("--add-data", str(ROOT / f"assets/audio/production/{name}.ogg") + os.pathsep + "assets/audio/production")],
        "--add-data", str(ROOT / "assets/manifest.json") + os.pathsep + "assets",
        "--add-data", str(ROOT / "LICENSE") + os.pathsep + ".",
    ])
    destination = ROOT / "dist/SystemPanic/paks"
    destination.mkdir(exist_ok=True)
    for manifest in sorted((ROOT / "paks").glob("*/pak.json")):
        shutil.copytree(manifest.parent, destination / manifest.parent.name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print("Built:", ROOT / "dist/SystemPanic/SystemPanic.exe")


if __name__ == "__main__":
    main()
