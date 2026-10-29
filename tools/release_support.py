"""Shared, import-safe release paths, metadata, integrity and cleanup helpers."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
AUDIO_NAMES = ("shot", "impact", "shuffle", "hurt", "clear", "select", "game_over")


def project_version(root: Path = ROOT) -> str:
    with (root / "pyproject.toml").open("rb") as source:
        version = tomllib.load(source)["project"]["version"]
    if not isinstance(version, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.!+_-]*", version):
        raise ValueError("Project version must be a safe, nonempty filename component")
    return version


def validate_tag(tag: str, version: str) -> None:
    if tag != "v" + version:
        raise ValueError(f"Release tag {tag!r} must equal 'v{version}' from pyproject.toml")


def _git(root: Path, *arguments: str) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(root), *arguments],
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def release_preflight(tag: str | None = None, root: Path = ROOT) -> dict:
    version = project_version(root)
    commit = _git(root, "rev-parse", "HEAD")
    status = _git(root, "status", "--porcelain", "--untracked-files=all")
    if tag is not None:
        validate_tag(tag, version)
        if commit is None or status is None:
            raise ValueError("Tagged releases require a readable Git checkout")
        if status:
            raise ValueError("Tagged releases require a clean tracked and untracked working tree")
        if _git(root, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}") != commit:
            raise ValueError(f"HEAD must be exactly the commit referenced by {tag}")
    return {"version": version, "tag": tag, "commit": commit,
            "dirty": bool(status) if status is not None else None}


def sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def safe_remove_tree(path: Path, allowed_root: Path) -> None:
    target, boundary = path.resolve(), allowed_root.resolve()
    if target == boundary or not target.is_relative_to(boundary):
        raise ValueError(f"Refusing cleanup outside a child of {boundary}: {target}")
    if path.is_symlink():
        raise ValueError(f"Refusing cleanup through a symlink: {path}")
    if target.exists():
        if not target.is_dir():
            raise ValueError(f"Cleanup target must be a directory: {target}")
        shutil.rmtree(target)


def file_inventory(folder: Path) -> dict[str, str]:
    return {path.relative_to(folder).as_posix(): sha256(path)
            for path in sorted(folder.rglob("*"))
            if path.is_file() and "__pycache__" not in path.relative_to(folder).parts
            and path.suffix != ".pyc"}


def verify_inventory(folder: Path, expected: dict[str, str]) -> None:
    actual = file_inventory(folder)
    missing, extra = set(expected) - set(actual), set(actual) - set(expected)
    changed = {name for name in set(expected) & set(actual) if expected[name] != actual[name]}
    if missing or extra or changed:
        raise ValueError(f"Inventory mismatch in {folder}: missing={sorted(missing)}, "
                         f"extra={sorted(extra)}, changed={sorted(changed)}")


def write_checksums(paths: list[Path], destination: Path) -> None:
    names = [path.name for path in paths]
    if len(set(names)) != len(names):
        raise ValueError("Checksum input basenames must be unique")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("".join(f"{sha256(path)}  {path.name}\n" for path in sorted(paths)), encoding="utf-8")


def verify_checksums(manifest: Path) -> dict[str, str]:
    records = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/\\]+)", line)
        if not match or match[2] in {".", ".."} or ":" in match[2] or match[2] in records:
            raise ValueError(f"Invalid or duplicate checksum record: {line!r}")
        digest, filename = match.groups()
        if sha256(manifest.parent / filename) != digest:
            raise ValueError(f"SHA-256 mismatch: {filename}")
        records[filename] = digest
    if not records:
        raise ValueError("Checksum manifest is empty")
    return records


def release_paths(version: str, root: Path = ROOT) -> dict[str, Path]:
    distribution = root / "dist"
    for name in ("dist", "build"):
        target = (root / name).resolve()
        if target == root.resolve() or not target.is_relative_to(root.resolve()):
            raise ValueError(f"The release {name} directory must resolve inside the project")
    if not (distribution / "SystemPanic").resolve().is_relative_to(distribution.resolve()):
        raise ValueError("The frozen folder must resolve inside the release dist directory")
    return {"folder": distribution / "SystemPanic",
            "archive": distribution / f"SystemPanic-v{version}-windows-x64.zip",
            "wheel": distribution / f"system_panic-{version}-py3-none-any.whl",
            "metadata": distribution / "BUILDINFO.json",
            "checksums": distribution / "SHA256SUMS.txt"}


def host_inventory(root: Path = ROOT) -> dict[str, str]:
    paths = [root / "play.py", root / "LICENSE", root / "assets/images/title.png",
             root / "assets/manifest.json", *sorted((root / "src/system_panic").rglob("*.py")),
             *(root / f"assets/audio/production/{name}.ogg" for name in AUDIO_NAMES)]
    return {path.relative_to(root).as_posix(): sha256(path) for path in paths}


def build_metadata(tag: str | None = None, root: Path = ROOT) -> dict:
    record = release_preflight(tag, root)
    toolchain = {}
    for name in ("pygame", "pyinstaller", "setuptools", "build"):
        try:
            toolchain[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            toolchain[name] = None
    record.update(built_at_utc=datetime.now(timezone.utc).isoformat(), python=sys.version,
                  platform=platform.platform(), architecture=platform.machine(),
                  toolchain=toolchain, host_files=host_inventory(root))
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Require vVERSION, clean checkout and HEAD at this exact tag")
    parser.add_argument("--check", action="store_true", help="Require --tag and run release preflight")
    args = parser.parse_args()
    if args.check and not args.tag:
        parser.error("--check requires --tag")
    print(json.dumps(release_preflight(args.tag), indent=2))


if __name__ == "__main__":
    main()
