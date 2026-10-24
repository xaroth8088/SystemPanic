"""Validated preferences and atomic local persistence."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
import os
from pathlib import Path
import tempfile

from .paks import PAKS, BY_ID, CHANNELS


@dataclass
class Preferences:
    enabled: list[str] = field(default_factory=lambda: list(BY_ID))
    mix_mode: str = "remix"
    shuffle_seconds: int = 8
    difficulty: str = "standard"
    endless: bool = False
    music: float = .55
    effects: float = .65
    reduced_motion: bool = False
    fullscreen: bool = False
    aim_assist: bool = True
    shuffle_channels: list[str] = field(default_factory=lambda: list(CHANNELS))
    high_score: int = 0

    @classmethod
    def from_dict(cls, raw):
        result = cls()
        if not isinstance(raw, dict):
            return result
        if isinstance(raw.get("enabled"), list):
            result.enabled = [p.id for p in PAKS if p.id in raw["enabled"]] or [PAKS[0].id]
        for name, choices in (("mix_mode", ("remix", "coherent")),
                              ("difficulty", ("relaxed", "standard", "intense"))):
            if raw.get(name) in choices:
                setattr(result, name, raw[name])
        for name in ("endless", "reduced_motion", "fullscreen", "aim_assist"):
            if type(raw.get(name)) is bool:
                setattr(result, name, raw[name])
        for name in ("music", "effects"):
            val = raw.get(name)
            if type(val) in (int, float) and math.isfinite(val):
                setattr(result, name, max(0., min(1., float(val))))
        val = raw.get("shuffle_seconds")
        if type(val) is int:
            result.shuffle_seconds = max(4, min(30, val))
        val = raw.get("high_score")
        if type(val) is int:
            result.high_score = max(0, min(999999999, val))
        if isinstance(raw.get("shuffle_channels"), list):
            result.shuffle_channels = [v for v in CHANNELS if v in raw["shuffle_channels"]]
        return result


def default_data_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "SystemPanic"


class PreferenceStore:
    def __init__(self, directory: Path | None = None):
        self.path = (directory or default_data_dir()) / "preferences.json"
        self.error = ""

    def load(self) -> Preferences:
        try:
            return Preferences.from_dict(json.loads(self.path.read_text(encoding="utf-8")))
        except FileNotFoundError:
            return Preferences()
        except (OSError, ValueError, TypeError) as exc:
            self.error = f"Could not read preferences: {exc}"
            return Preferences()

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
