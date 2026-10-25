"""Validated preferences and atomic local persistence."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path
import tempfile

from .paks import get_catalog, CHANNELS
from .resources import data_root

RENDER_RESOLUTIONS = ("auto", "960x600", "1024x768", "1280x720", "1280x800", "1600x900",
                      "1600x1000", "1920x1080", "1920x1200", "2560x1440", "2560x1600", "3840x2160")


@dataclass
class Preferences:
    schema_version: int = 2
    enabled: list[str] = field(default_factory=lambda: list(get_catalog().by_id))
    mix_mode: str = "remix"
    shuffle_seconds: int = 8
    difficulty: str = "standard"
    music: float = .55
    effects: float = .65
    reduced_motion: bool = False
    fullscreen: bool = False
    render_resolution: str = "auto"
    aim_assist: bool = True
    gamepad_deadzone: float = .18
    shuffle_channels: list[str] = field(default_factory=lambda: list(CHANNELS))
    high_score: int = 0

    @classmethod
    def from_dict(cls, raw, catalog=None):
        catalog = catalog if catalog is not None else get_catalog()
        result = cls(enabled=list(catalog.by_id))
        if not isinstance(raw, dict):
            return result
        if isinstance(raw.get("enabled"), list):
            result.enabled = [p.id for p in catalog.paks if p.id in raw["enabled"]]
            # Removed Paks cannot leave stale IDs or an unplayable selection.
            for channel in CHANNELS:
                if not catalog.providers(channel, result.enabled):
                    providers = catalog.providers(channel)
                    if providers:
                        result.enabled.append(providers[0])
        for name, choices in (("mix_mode", ("remix", "coherent")),
                              ("difficulty", ("relaxed", "standard", "intense"))):
            if raw.get(name) in choices:
                setattr(result, name, raw[name])
        for name in ("reduced_motion", "fullscreen", "aim_assist"):
            if type(raw.get(name)) is bool:
                setattr(result, name, raw[name])
        val = raw.get("render_resolution")
        if type(val) is str and val in RENDER_RESOLUTIONS:
            result.render_resolution = val
        for name in ("music", "effects"):
            val = raw.get(name)
            if type(val) in (int, float) and math.isfinite(val):
                setattr(result, name, max(0., min(1., float(val))))
        val = raw.get("gamepad_deadzone")
        if type(val) in (int, float) and math.isfinite(val):
            result.gamepad_deadzone = max(.05, min(.45, float(val)))
        val = raw.get("shuffle_seconds")
        if type(val) is int:
            result.shuffle_seconds = max(4, min(30, val))
        val = raw.get("high_score")
        if type(val) is int:
            result.high_score = max(0, min(999999999, val))
        if isinstance(raw.get("shuffle_channels"), list):
            channels = raw["shuffle_channels"].copy()
            if raw.get("schema_version") != 2:
                if "arena" in channels:
                    channels.extend(["background", "obstacles"])
                if "pilot" in channels:
                    channels.append("music")
            result.shuffle_channels = [v for v in CHANNELS if v in channels]
        if result.mix_mode == "coherent" and not catalog.complete_ids(result.enabled):
            result.mix_mode = "remix"
        return result


def default_data_dir() -> Path:
    return data_root()


class PreferenceStore:
    def __init__(self, directory: Path | None = None, catalog=None):
        self.catalog = catalog if catalog is not None else get_catalog()
        self.path = (directory or default_data_dir()) / "preferences.json"
        self.error = ""

    def load(self) -> Preferences:
        try:
            return Preferences.from_dict(json.loads(self.path.read_text(encoding="utf-8")), self.catalog)
        except FileNotFoundError:
            return Preferences.from_dict({}, self.catalog)
        except (OSError, ValueError, TypeError) as exc:
            self.error = f"Could not read preferences: {exc}"
            return Preferences.from_dict({}, self.catalog)

    def save(self, prefs: Preferences) -> bool:
        temp_path = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix="prefs-", suffix=".tmp", delete=False) as stream:
                temp_path = Path(stream.name)
                json.dump(asdict(prefs), stream, indent=2, allow_nan=False)
                stream.write("\n")
            temp_path.replace(self.path)
            self.error = ""
            return True
        except (OSError, ValueError, TypeError) as exc:
            self.error = f"Could not save preferences: {exc}"
            if temp_path:
                temp_path.unlink(missing_ok=True)
            return False
