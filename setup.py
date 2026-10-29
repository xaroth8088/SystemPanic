"""Preserve discovered Pak folder trees as external data in installed distributions."""
from collections import defaultdict
from pathlib import Path
from setuptools import setup

root = Path(__file__).parent
groups = defaultdict(list)
for path in sorted((root / "paks").rglob("*")):
    if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
        groups["share/system-panic/" + path.parent.relative_to(root).as_posix()].append(path.relative_to(root).as_posix())
for relative in ("images/title.png", "manifest.json", *(f"audio/production/{name}.ogg" for name in ("shot", "impact", "shuffle", "hurt", "clear", "select", "game_over"))):
    path = root / "assets" / relative
    groups["share/system-panic/" + Path(relative).parent.as_posix()].append(path.relative_to(root).as_posix())
setup(data_files=list(groups.items()))
