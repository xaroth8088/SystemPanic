"""Create a runnable Pak to learn from, copying selected component folders."""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from system_panic.paks import CHANNELS


def create_pak(destination: Path, source: Path, components=CHANNELS):
    """Never overwrite a directory; copied components/assets remain independent."""
    id = destination.name
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", id):
        raise ValueError("Use a lowercase Pak directory name containing letters, digits and underscores")
    if destination.exists():
        raise ValueError("Destination already exists")
    components = tuple(dict.fromkeys(components))
    if not components or any(c not in CHANNELS for c in components):
        raise ValueError("Select one or more valid component types")
    data = json.loads((source / "pak.json").read_text(encoding="utf-8"))
    for channel in components:
        if not (source / channel).is_dir():
            raise ValueError(f"Source Pak does not provide {channel}")
    destination.mkdir()
    for channel in components:
        shutil.copytree(source / channel, destination / channel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    selected = {c:data["components"][c] for c in components} if isinstance(data.get("components"), dict) else list(components)
    data.update(id=id, name=id.replace("_", " ").title(), version="0.1.0", order=100,
                description="A local starting point: edit the component classes and their assets.", components=selected)
    data.pop("authoring", None)
    data["asset_provenance"] = {"copied_from":str(source.resolve()), "note":"Starter assets are copies of the source Pak's recorded AI assets. Replace and record your own when authoring."}
    (destination / "pak.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (destination / "AGENTS.md").write_text("# Pak authoring memory\n\nEach component owns its code and local assets. Subclass the corresponding ABC in `system_panic.pak_api`. Keep asset handles in attributes of your own choosing; return them through the documented methods. Test this Pak alone if complete, and in eligible mixes. Record original asset provenance when replacing starter assets.\n", encoding="utf-8")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--from-pak", type=Path, default=ROOT / "paks/signal_runner")
    parser.add_argument("--components", nargs="+", choices=CHANNELS, default=list(CHANNELS))
    args = parser.parse_args()
    try:
        result = create_pak(args.directory, args.from_pak, args.components)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"Created {result}. Edit its component classes, then rescan Paks in the game.")


if __name__ == "__main__":
    main()
