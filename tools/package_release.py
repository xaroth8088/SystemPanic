"""Package a fresh Windows folder and wheel, with exact content checks and SHA-256."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

try:
    from .release_support import (AUDIO_NAMES, ROOT, file_inventory, host_inventory,
                                 release_paths, release_preflight, safe_remove_tree,
                                 sha256, verify_checksums, verify_inventory, write_checksums)
except ImportError:  # Direct script execution.
    from release_support import (AUDIO_NAMES, ROOT, file_inventory, host_inventory,
                                 release_paths, release_preflight, safe_remove_tree,
                                 sha256, verify_checksums, verify_inventory, write_checksums)


def verify_wheel(wheel: Path, pak_files: dict[str, str]) -> None:
    with zipfile.ZipFile(wheel) as bundle:
        if bundle.testzip() is not None:
            raise ValueError("Wheel CRC check failed")
        members = bundle.namelist()
        if len(members) != len(set(members)):
            raise ValueError("Wheel contains duplicate members")
        marker = ".data/data/share/system-panic/paks/"
        actual = {name.split(marker, 1)[1]: name for name in members if marker in name and not name.endswith("/")}
        if set(actual) != set(pak_files):
            raise ValueError("Wheel Pak file set differs from source")
        for relative, digest in pak_files.items():
            if hashlib.sha256(bundle.read(actual[relative])).hexdigest() != digest:
                raise ValueError(f"Wheel Pak differs from source: {relative}")
        sources = sorted((ROOT / "src/system_panic").rglob("*.py"))
        expected_code = {source.relative_to(ROOT / "src").as_posix() for source in sources}
        actual_code = {name for name in members if name.startswith("system_panic/") and name.endswith(".py")}
        if actual_code != expected_code:
            raise ValueError("Wheel runtime module set differs from source")
        for source in sources:
            if bundle.read(source.relative_to(ROOT / "src").as_posix()) != source.read_bytes():
                raise ValueError(f"Wheel runtime differs from source: {source}")
        production = ("images/title.png", "manifest.json",
                      *(f"audio/production/{name}.ogg" for name in AUDIO_NAMES))
        for relative in production:
            suffix = ".data/data/share/system-panic/" + relative
            found = [name for name in members if name.endswith(suffix)]
            if len(found) != 1 or bundle.read(found[0]) != (ROOT / "assets" / relative).read_bytes():
                raise ValueError(f"Wheel production asset differs from source: {relative}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Validate a clean tagged release before packaging")
    args = parser.parse_args()
    revision = release_preflight(args.tag)
    paths = release_paths(revision["version"])
    folder = paths["folder"]
    output = ROOT / "output/release"
    output.mkdir(parents=True, exist_ok=True)
    paths["wheel"].parent.mkdir(parents=True, exist_ok=True)
    if not (folder / "SystemPanic.exe").is_file():
        raise SystemExit("Build the Windows folder first: python tools/build.py")
    record = json.loads((folder / "BUILDINFO.json").read_text(encoding="utf-8"))
    if any(record.get(key) != revision[key] for key in ("version", "commit")):
        raise ValueError("Built executable version/commit differs from this checkout; rebuild first")
    if record.get("host_files") != host_inventory():
        raise ValueError("Runtime/assets changed since the executable build; rebuild first")
    if args.tag and record.get("dirty") is not False:
        raise ValueError("A tagged release must be built from a clean checkout")
    record["tag"] = args.tag

    # Replace the complete external tree, including removal of deleted Pak files.
    pak_files = file_inventory(ROOT / "paks")
    destination = folder / "paks"
    safe_remove_tree(destination, folder)
    shutil.copytree(ROOT / "paks", destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    verify_inventory(destination, pak_files)
    record["pak_files"] = pak_files
    (folder / "BUILDINFO.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    paths["metadata"].write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    # A fresh wheel output prevents accidental selection of an earlier version.
    safe_remove_tree(ROOT / "build/lib", ROOT / "build")
    with tempfile.TemporaryDirectory(prefix="system-panic-wheel-", dir=output) as temporary:
        with (output / "wheel-build.log").open("w", encoding="utf-8") as log:
            subprocess.run([sys.executable, "-m", "build", "--wheel", "--no-isolation",
                            "--outdir", temporary], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        wheels = list(Path(temporary).glob("*.whl"))
        if len(wheels) != 1 or wheels[0].name != paths["wheel"].name:
            raise ValueError(f"Unexpected wheel output: {[path.name for path in wheels]}")
        shutil.copyfile(wheels[0], paths["wheel"])
    verify_wheel(paths["wheel"], pak_files)

    inventory = file_inventory(folder)
    archive = Path(shutil.make_archive(str(paths["archive"].with_suffix("")), "zip",
                                      root_dir=folder.parent, base_dir=folder.name))
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError("Release ZIP CRC check failed")
        members = {name[len("SystemPanic/"):]: name for name in bundle.namelist()
                   if name.startswith("SystemPanic/") and not name.endswith("/")
                   and "__pycache__" not in Path(name).parts and not name.endswith(".pyc")}
        if set(members) != set(inventory):
            raise ValueError("Release ZIP file set differs from built folder")
        for name, digest in inventory.items():
            if hashlib.sha256(bundle.read(members[name])).hexdigest() != digest:
                raise ValueError(f"Release ZIP differs from built folder: {name}")
    write_checksums([archive, paths["wheel"], paths["metadata"]], paths["checksums"])
    verify_checksums(paths["checksums"])
    report = {"version": revision["version"], "source_pak_files": len(pak_files),
              "windows_matches_source": True, "wheel_matches_source": True,
              "zip_matches_source": True, "zip_crc": True,
              "executable_sha256": sha256(folder / "SystemPanic.exe"),
              "wheel_sha256": sha256(paths["wheel"]), "zip_sha256": sha256(archive)}
    (output / "packaging.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
