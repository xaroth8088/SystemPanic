"""Discover API 2 component folders and concrete ABC implementations."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property, lru_cache
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import inspect
import itertools
import json
from pathlib import Path
import re
import sys
from types import MappingProxyType, ModuleType
from typing import cast

from .model import Pak, ComponentSpec, CHANNELS
from ..pak_api import ComponentBase, PilotBase, EnemyBase, WeaponBase, MusicBase, BackgroundBase, ObstaclesBase, ImageAsset, SoundAsset, SpriteFrame
from ..resources import pak_roots

API_VERSION = 3
BASES = dict(zip(CHANNELS, (PilotBase, EnemyBase, WeaponBase, MusicBase, BackgroundBase, ObstaclesBase)))
FILENAMES = {c: c + ".py" for c in CHANNELS} | {"obstacles":"obstacle.py"}
_generation = itertools.count()


class _FreshSource(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname):
        return compile(self.get_data(self.path), self.path, "exec")


class _PakImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if not fullname.startswith("_system_panic_pak_"):
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec and spec.origin and isinstance(spec.loader, importlib.machinery.SourceFileLoader):
            spec.loader = _FreshSource(fullname, spec.origin)
        return spec


sys.meta_path.insert(0, _PakImports())


@dataclass(frozen=True)
class PakIssue:
    path: Path
    message: str


@dataclass(frozen=True)
class Catalog:
    paks: tuple[Pak, ...]
    issues: tuple[PakIssue, ...]
    roots: tuple[Path, ...]

    @cached_property
    def by_id(self):
        return MappingProxyType({pak.id: pak for pak in self.paks})

    def providers(self, channel, enabled=None):
        return tuple(pak.id for pak in self.paks if channel in pak.parts and (enabled is None or pak.id in enabled))

    def missing(self, enabled):
        return tuple(c for c in CHANNELS if not self.providers(c, enabled))

    def complete_ids(self, enabled=None):
        return tuple(pak.id for pak in self.paks if pak.complete and (enabled is None or pak.id in enabled))

def local_file(directory, name, suffixes=None):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError("Paths must be relative to the component folder")
    path = (directory / name).resolve()
    if not path.is_relative_to(directory) or not path.is_file() or (suffixes and path.suffix.lower() not in suffixes):
        raise ValueError(f"Missing, unsupported or out-of-folder file: {name}")
    return path


def read_manifest(directory):
    path = directory / "pak.json"
    if path.stat().st_size > 65536:
        raise ValueError("Manifest exceeds 64 KiB")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or type(data.get("api_version")) is not int or data["api_version"] != API_VERSION:
        raise ValueError(f"Unsupported Pak API; expected api_version {API_VERSION} with component folders")
    if not isinstance(data.get("id"), str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", data["id"]):
        raise ValueError("ID must be a lowercase identifier of at most 64 characters")
    for field in ("name", "version", "subtitle", "description"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > 500 or any(ord(c) < 32 for c in value):
            raise ValueError(f"Missing or invalid text field: {field}")
    color = data.get("color")
    if not isinstance(color, list) or len(color) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in color):
        raise ValueError("color must contain three integers from 0 to 255")
    if type(data.get("order", 100)) is not int:
        raise ValueError("order must be an integer")
    components = data.get("components", [c for c in CHANNELS if (directory / c).is_dir()])
    if isinstance(components, list):
        if any(not isinstance(c, str) for c in components) or len(set(components)) != len(components):
            raise ValueError("components must contain distinct component names")
        components = {c:{} for c in components}
    if not isinstance(components, dict) or not components or any(c not in CHANNELS for c in components):
        raise ValueError("components must select pilot, enemy, weapon, music, background or obstacles")
    for channel, config in components.items():
        folder = (directory / channel).resolve()
        if not folder.is_relative_to(directory) or not folder.is_dir() or not isinstance(config, dict):
            raise ValueError(f"Missing or invalid component folder: {channel}")
        if config.get("inherits") is not None and not isinstance(config["inherits"], str):
            raise ValueError(f"Invalid inheritance provider: {channel}")
        if config.get("class") is not None and not isinstance(config["class"], str):
            raise ValueError(f"Invalid class name: {channel}")
        if not isinstance(config.get("assets", {}), dict):
            raise ValueError(f"Invalid asset overrides: {channel}")
        for alias, filename in config.get("assets", {}).items():
            if not isinstance(alias, str) or not alias or Path(alias).is_absolute() or not (folder / alias).resolve().is_relative_to(folder):
                raise ValueError(f"Invalid asset alias: {alias}")
            local_file(folder, filename, (".png", ".webp", ".jpg", ".jpeg", ".ogg", ".wav"))
        if not config.get("inherits"):
            local_file(folder, FILENAMES[channel], (".py",))
    return data, components


def import_component(package, channel, folder):
    name = package + "." + channel
    entry = folder / FILENAMES[channel]
    spec = importlib.util.spec_from_file_location(name, entry, submodule_search_locations=[str(folder)])
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load component: {channel}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(entry.read_bytes(), str(entry), "exec"), module.__dict__)
    return module


def load_pak(directory, data, configs, loaded):
    name = "_system_panic_pak_" + hashlib.sha256(str(directory).encode()).hexdigest()[:16] + f"_{next(_generation)}"
    package = ModuleType(name)
    package.__path__ = [str(directory)]
    package.__spec__ = importlib.util.spec_from_loader(name, loader=None, is_package=True)
    sys.modules[name] = package
    parts = {}
    try:
        for channel in CHANNELS:
            if channel not in configs:
                continue
            config = configs[channel]
            folder = (directory / channel).resolve()
            overrides = {}
            if config.get("inherits"):
                provider = loaded.get(config["inherits"])
                if provider is None or channel not in provider.parts:
                    raise ValueError(f"Missing {channel} provider: {config['inherits']}")
                base = provider.parts[channel]
                implementation, asset_root = base.implementation, base.directory
                overrides.update(base.overrides)
            else:
                module = import_component(name, channel, folder)
                implementation = getattr(module, config.get("class", "COMPONENT"), None)
                if implementation is None:
                    candidates = [value for value in vars(module).values() if inspect.isclass(value)
                                  and value.__module__ == module.__name__ and issubclass(value, BASES[channel])]
                    if len(candidates) != 1:
                        raise ValueError(f"{channel}: define one {BASES[channel].__name__} subclass or export COMPONENT")
                    implementation = candidates[0]
                if not inspect.isclass(implementation) or not issubclass(cast(type, implementation), BASES[channel]):
                    raise ValueError(f"{channel}: expected a {BASES[channel].__name__} subclass")
                implementation = cast(type[ComponentBase], implementation)
                missing_methods = getattr(implementation, "__abstractmethods__", ())
                if missing_methods:
                    raise ValueError(f"{channel}: abstract methods missing: {', '.join(sorted(missing_methods))}")
                asset_root = folder
            overrides.update({alias:local_file(folder, filename) for alias, filename in config.get("assets", {}).items()})
            definition = ComponentSpec(implementation, asset_root, MappingProxyType(overrides))
            probe = definition.create()
            preview = probe.preview()
            if preview is not None and not isinstance(preview, (ImageAsset, SpriteFrame)):
                raise ValueError("preview/sprite must return an ImageAsset, SpriteFrame or None")
            if isinstance(probe, MusicBase):
                track = probe.track()
                if track is not None and not isinstance(track, SoundAsset):
                    raise ValueError("MusicBase.track must return a SoundAsset or None")
            if channel == "pilot" and any(not isinstance(getattr(probe, field), str) or len(getattr(probe, field)) > 500 for field in ("controls", "special")):
                raise ValueError("Pilot controls and special must be text")
            probe.suspend()
            parts[channel] = definition
        metadata = {key:data[key] for key in ("id", "name", "version", "subtitle", "description")}
        return Pak(**metadata, directory=directory, color=(data["color"][0], data["color"][1], data["color"][2]), parts=MappingProxyType(parts))
    except BaseException:
        for key in tuple(sys.modules):
            if key == name or key.startswith(name + "."):
                del sys.modules[key]
        raise


def discover(roots=None):
    roots = tuple(dict.fromkeys(Path(path).resolve() for path in (pak_roots() if roots is None else roots)))
    pending, issues, loaded = {}, [], {}
    for root in roots:
        if not root.exists():
            continue
        try:
            directories = sorted(path for path in root.iterdir() if path.is_dir() and (path / "pak.json").is_file())
        except OSError as exc:
            issues.append(PakIssue(root, str(exc)))
            continue
        for directory in directories:
            directory = directory.resolve()
            try:
                record = read_manifest(directory)
                if record[0]["id"] in pending:
                    raise ValueError(f"Duplicate Pak ID: {record[0]['id']}; the first manifest wins")
                pending[record[0]["id"]] = (directory, record)
            except (Exception, SystemExit) as exc:
                issues.append(PakIssue(directory, f"{type(exc).__name__}: {exc}"))
    orders = {id:record[0].get("order", 100) for id, (_, record) in pending.items()}
    while pending:
        progressed = False
        for id, (directory, (data, configs)) in tuple(pending.items()):
            dependencies = [config["inherits"] for config in configs.values() if config.get("inherits")]
            if any(base not in loaded and base in pending for base in dependencies):
                continue
            try:
                loaded[id] = load_pak(directory, data, configs, loaded)
            except (Exception, SystemExit) as exc:
                issues.append(PakIssue(directory, f"{type(exc).__name__}: {exc}"))
            del pending[id]
            progressed = True
        if not progressed:
            issues.extend(PakIssue(directory, "Cyclic Pak inheritance dependency") for directory, _ in pending.values())
            break
    return Catalog(tuple(sorted(loaded.values(), key=lambda pak: (orders[pak.id], pak.id))), tuple(issues), roots)


@lru_cache(maxsize=1)
def get_catalog():
    return discover()
