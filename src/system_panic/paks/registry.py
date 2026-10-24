"""Discovery and validation for trusted local Pak folders, including partial Paks."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property, lru_cache
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import itertools
import json
import math
from pathlib import Path
import re
import sys
from types import MappingProxyType

from .model import Pak
from ..resources import pak_roots

API_VERSION = 1
CHANNELS = ("pilot", "weapon", "enemy", "arena")
SPRITE_CHANNELS = ("pilot", "enemy", "arena", "weapon")
CALLBACKS = {"pilot": ("move", "prepare_pilot", "demo_controls"), "weapon": ("fire",),
             "enemy": ("advance_enemy",), "arena": ("make_arena", "draw_arena")}
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


# Restrict fresh-source loading to Pak namespaces; ordinary game imports retain
# their normal behavior. Helper edits are visible even with unchanged mtimes.
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
        return tuple(pak.id for pak in self.paks if channel in pak.components and (enabled is None or pak.id in enabled))

    def missing(self, enabled):
        return tuple(channel for channel in CHANNELS if not self.providers(channel, enabled))

    def complete_ids(self, enabled=None):
        return tuple(pak.id for pak in self.paks if pak.complete and (enabled is None or pak.id in enabled))


def local_file(directory, name, suffixes):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError("File paths must be relative to the Pak folder")
    path = (directory / name).resolve()
    if not path.is_relative_to(directory) or path.suffix.lower() not in suffixes or not path.is_file():
        raise ValueError(f"Missing, unsupported or out-of-folder file: {name}")
    return path


def read_manifest(directory):
    path = directory / "pak.json"
    if path.stat().st_size > 65536:
        raise ValueError("Manifest exceeds 64 KiB")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or type(data.get("api_version")) is not int or data["api_version"] != API_VERSION:
        raise ValueError(f"Unsupported Pak API; expected api_version {API_VERSION}")
    if not isinstance(data.get("id"), str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", data["id"]):
        raise ValueError("ID must be a lowercase identifier of at most 64 characters")
    for field in ("name", "version", "subtitle", "description"):
        if not isinstance(data.get(field), str) or not data[field].strip() or len(data[field]) > 500:
            raise ValueError(f"Missing or invalid text field: {field}")
    for field in ("name", "version", "subtitle", "description", "controls", "special", *CHANNELS):
        if field in data and (not isinstance(data[field], str) or len(data[field]) > 500 or any(ord(c) < 32 for c in data[field])):
            raise ValueError(f"Invalid text field: {field}")
    components = data.get("components")
    if not isinstance(components, list) or not components or any(c not in CHANNELS for c in components) or len(set(components)) != len(components):
        raise ValueError("components must list one or more distinct pilot, weapon, enemy or arena channels")
    inherits = data.get("inherits", {})
    if not isinstance(inherits, dict) or any(c not in components or not isinstance(base, str) for c, base in inherits.items()):
        raise ValueError("inherits must map supplied components to installed Pak IDs")
    for field in components:
        if field not in inherits and (not isinstance(data.get(field), str) or not data[field].strip()):
            raise ValueError(f"Missing behavior label: {field}")
    if "pilot" in components and "pilot" not in inherits:
        for field in ("controls", "special"):
            if not isinstance(data.get(field), str) or not data[field].strip():
                raise ValueError(f"Missing pilot text: {field}")
    color = data.get("color")
    if not isinstance(color, list) or len(color) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in color):
        raise ValueError("color must contain three integers from 0 to 255")
    cooldown = data.get("cooldown", .25)
    if type(cooldown) not in (int, float) or not math.isfinite(cooldown) or cooldown <= 0:
        raise ValueError("cooldown must be a positive finite number")
    if type(data.get("splits", 0)) is not int or not 0 <= data.get("splits", 0) <= 32:
        raise ValueError("splits must be an integer from 0 to 32")
    if type(data.get("order", 100)) is not int:
        raise ValueError("order must be an integer")
    presentation = data.get("presentation", {})
    if not isinstance(presentation, dict) or presentation.get("pilot_sprite", "upright") not in ("upright", "rotate", "face") or type(presentation.get("rotate_enemy", False)) is not bool:
        raise ValueError("Invalid presentation settings")
    assets = data.get("assets")
    if not isinstance(assets, dict) or not isinstance(assets.get("sprites"), dict):
        raise ValueError("assets.sprites must map supplied components to image paths")
    sprites = tuple(local_file(directory, assets["sprites"].get(c), (".png", ".webp")) if c in components else None for c in SPRITE_CHANNELS)
    music = local_file(directory, assets["music"], (".ogg", ".wav")) if assets.get("music") else None
    entry = local_file(directory, data.get("entrypoint", "pak.py"), (".py",)) if set(components) - set(inherits) else None
    return data, entry, sprites, music


def load_pak(directory, data, entry, sprites, music, bases):
    callbacks, values = {}, {}
    module = None
    name = "_system_panic_pak_" + hashlib.sha256(str(directory).encode()).hexdigest()[:16] + f"_{next(_generation)}"
    try:
        if entry:
            spec = importlib.util.spec_from_file_location(name, entry, submodule_search_locations=[str(directory)])
            if spec is None or spec.loader is None:
                raise ValueError("Could not load the Python entrypoint")
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            # Recompile on rescan rather than using timestamp-sensitive bytecode.
            exec(compile(entry.read_text(encoding="utf-8-sig"), str(entry), "exec"), module.__dict__)
        for channel in data["components"]:
            base = bases.get(channel)
            values[channel] = data.get(channel, getattr(base, channel, ""))
            for index, field in enumerate(CALLBACKS[channel]):
                callback = getattr(base if base else module, field, None)
                if (index == 0 and not callable(callback)) or (callback is not None and not callable(callback)):
                    raise ValueError(f"Missing or invalid callback: {field}")
                callbacks[field] = callback
        pilot, weapon, enemy = (bases.get(c) for c in ("pilot", "weapon", "enemy"))
        presentation = data.get("presentation", {})
        metadata = {key:data[key] for key in ("id", "name", "version", "subtitle", "description")}
        return Pak(**metadata, **values, directory=directory, components=tuple(c for c in CHANNELS if c in data["components"]),
                   color=(data["color"][0], data["color"][1], data["color"][2]), sprites=sprites, music=music, **callbacks,
                   controls=data.get("controls", getattr(pilot, "controls", "")), special=data.get("special", getattr(pilot, "special", "")),
                   cooldown=data.get("cooldown", getattr(weapon, "cooldown", .25)), splits=data.get("splits", getattr(enemy, "splits", 0)),
                   pilot_sprite=presentation.get("pilot_sprite", getattr(pilot, "pilot_sprite", "upright")),
                   rotate_enemy=presentation.get("rotate_enemy", getattr(enemy, "rotate_enemy", False)))
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
                data = record[0]
                if data["id"] in pending:
                    raise ValueError(f"Duplicate Pak ID: {data['id']}; the first manifest wins")
                pending[data["id"]] = (directory, record)
            except (Exception, SystemExit) as exc:
                issues.append(PakIssue(directory, f"{type(exc).__name__}: {exc}"))
    orders = {id:record[0].get("order", 100) for id, (_, record) in pending.items()}
    while pending:
        progressed = False
        for id, (directory, (data, entry, sprites, music)) in tuple(pending.items()):
            inherits = data.get("inherits", {})
            if any(base not in loaded and base in pending for base in inherits.values()):
                continue
            try:
                bases = {}
                for channel, base_id in inherits.items():
                    if base_id not in loaded or channel not in loaded[base_id].components:
                        raise ValueError(f"Missing {channel} provider: {base_id}")
                    bases[channel] = loaded[base_id]
                loaded[id] = load_pak(directory, data, entry, sprites, music, bases)
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
