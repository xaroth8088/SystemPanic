"""Smoke-test the actual extracted release ZIP and a fresh isolated wheel install."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import venv
import zipfile

try:
    from .release_support import (ROOT, file_inventory, host_inventory, release_paths, release_preflight,
                                 sha256, verify_checksums, verify_inventory)
except ImportError:  # Direct script execution.
    from release_support import (ROOT, file_inventory, host_inventory, release_paths, release_preflight,
                                 sha256, verify_checksums, verify_inventory)


def extract_release(archive: Path, destination: Path) -> Path:
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError("Release ZIP CRC check failed")
        names = bundle.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP members")
        for name in names:
            path = PurePosixPath(name)
            if ("\\" in name or ":" in name or path.is_absolute() or ".." in path.parts
                    or not path.parts or path.parts[0] != "SystemPanic"):
                raise ValueError(f"Unsafe or unexpected release ZIP member: {name}")
        bundle.extractall(destination)
    folder = destination / "SystemPanic"
    if not (folder / "SystemPanic.exe").is_file():
        raise ValueError("Release ZIP is missing SystemPanic/SystemPanic.exe")
    return folder


def verify_installed_wheel(wheel: Path, temporary: Path, output: Path,
                           wheelhouse: Path | None = None) -> dict:
    environment = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME"):
        environment.pop(name, None)
    environment.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
                       PYGAME_HIDE_SUPPORT_PROMPT="1", PIP_DISABLE_PIP_VERSION_CHECK="1",
                       LOCALAPPDATA=str(temporary / "user-data"),
                       XDG_DATA_HOME=str(temporary / "user-data"))
    prefix = temporary / "installed"
    venv.EnvBuilder(with_pip=True).create(prefix)
    python = prefix / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    working = temporary / "wheel-work"
    working.mkdir()
    command = [str(python), "-I", "-m", "pip", "install", "--only-binary=:all:"]
    if wheelhouse is not None:
        command += ["--no-index", "--find-links", str(wheelhouse.resolve())]
    command.append(str(wheel.resolve()))
    with (output / "wheel-install.log").open("w", encoding="utf-8") as log:
        subprocess.run(command, cwd=working, env=environment, stdout=log,
                       stderr=subprocess.STDOUT, timeout=180, check=True)

    # -I and a new venv keep the checkout and the build environment out of imports.
    inspect = '''
import importlib.metadata as metadata
import json
from pathlib import Path
import sys
import system_panic
from system_panic.paks.registry import discover
from system_panic.resources import pak_roots
installed = {d.metadata["Name"].lower().replace("_", "-"): d.version for d in metadata.distributions()}
assert set(installed) <= {"system-panic", "pygame", "pip", "setuptools"}, installed
assert {"system-panic", "pygame"} <= set(installed), installed
assert Path(system_panic.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
assert pak_roots()[0] == Path(sys.prefix) / "share/system-panic/paks", pak_roots()
catalog = discover()
assert not catalog.issues, catalog.issues
print(json.dumps({"packages": installed, "paks": list(catalog.complete_ids()), "prefix": sys.prefix}))
'''
    result = subprocess.run([str(python), "-I", "-c", inspect], cwd=working, env=environment,
                            capture_output=True, text=True, timeout=40, check=True)
    record = json.loads(result.stdout)
    expected = sorted(json.loads(path.read_text(encoding="utf-8"))["id"]
                      for path in (ROOT / "paks").glob("*/pak.json")
                      if len(json.loads(path.read_text(encoding="utf-8"))["components"]) == 6)
    if sorted(record["paks"]) != expected:
        raise ValueError("Installed wheel complete Pak IDs differ from source")
    # Verify the installed external files, not only the wheel's internal names.
    verify_inventory(prefix / "share/system-panic/paks", file_inventory(ROOT / "paks"))
    record["checks"] = []
    for pak in expected:
        screenshot = output / f"wheel-{pak}.png"
        command = [str(python), "-I", "-c", "from system_panic.app import main; main()",
                   "--headless", "--seed", "24", "--frames", "240", "--demo", "--solo", pak,
                   "--data-dir", str(temporary / "wheel-profile"), "--screenshot", str(screenshot)]
        completed = subprocess.run(command, cwd=working, env=environment,
                                   capture_output=True, text=True, timeout=40)
        if completed.returncode:
            raise ValueError(f"Installed wheel {pak} failed: {completed.stdout}\n{completed.stderr}")
        if not screenshot.is_file():
            raise ValueError(f"Installed wheel {pak} did not create its screenshot")
        record["checks"].append({"pak": pak, "frames": 240, "exit_code": completed.returncode})
        print(f"Installed wheel {pak}: passed", flush=True)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Validate the clean release tag before verification")
    parser.add_argument("--archive", type=Path, help="Release ZIP (defaults to current project version)")
    parser.add_argument("--wheel", type=Path, help="Wheel (defaults to current project version)")
    parser.add_argument("--wheelhouse", type=Path, help="Install dependencies offline from this directory")
    parser.add_argument("--output", type=Path, default=ROOT / "output/release-verification")
    args = parser.parse_args()
    revision = release_preflight(args.tag)
    paths = release_paths(revision["version"])
    archive, wheel = (args.archive or paths["archive"]).resolve(), (args.wheel or paths["wheel"]).resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    checksums = verify_checksums(paths["checksums"])
    if not {archive.name, wheel.name, paths["metadata"].name} <= set(checksums):
        raise ValueError("Checksum manifest does not cover all release assets")
    for artifact in (archive, wheel):
        if sha256(artifact) != checksums[artifact.name]:
            raise ValueError(f"Selected artifact does not match release checksums: {artifact}")
    metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
    if any(metadata.get(key) != revision[key] for key in ("version", "commit")):
        raise ValueError("Release metadata differs from current checkout")
    if metadata.get("host_files") != host_inventory():
        raise ValueError("Release runtime/assets differ from current checkout")
    if args.tag and metadata.get("tag") != args.tag:
        raise ValueError("Release metadata does not match the requested tag")
    with tempfile.TemporaryDirectory(prefix="release-", dir=output) as directory:
        temporary = Path(directory)
        folder = extract_release(archive, temporary / "extracted")
        if json.loads((folder / "BUILDINFO.json").read_text(encoding="utf-8")) != metadata:
            raise ValueError("Extracted build metadata differs from release metadata")
        verify_inventory(folder / "paks", file_inventory(ROOT / "paks"))
        environment = os.environ.copy()
        environment.update(LOCALAPPDATA=str(temporary / "frozen-user-data"),
                           XDG_DATA_HOME=str(temporary / "frozen-user-data"))
        subprocess.run([sys.executable, str(ROOT / "tools/verify_distribution.py"),
                        "--folder", str(folder), "--wheel", str(wheel),
                        "--output", str(output / "distribution")], cwd=temporary,
                       env=environment, check=True)
        installed = verify_installed_wheel(wheel, temporary, output, args.wheelhouse)
    report = {"version": revision["version"], "tag": args.tag,
              "checksums_verified": checksums, "extracted_zip_frozen_probes": True,
              "installed_wheel": installed}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Extracted release ZIP and freshly installed wheel passed all release checks.")


if __name__ == "__main__":
    main()
