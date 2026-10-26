"""Named, local six-channel combinations, independent of shuffle preferences."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import tempfile

from .paks import CHANNELS, get_catalog
from .resources import data_root

MAX_NAME_LENGTH = 48
_PAK_ID = re.compile(r"[a-z][a-z0-9_]{0,63}")
_REMIX_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")


@dataclass
class Remix:
    id: str
    name: str
    mix: dict[str, str]


def normalize_name(name: str) -> str:
    """Return a single-line display name, rejecting empty/non-text input."""
    if not isinstance(name, str):
        raise ValueError("Give the Remix a name.")
    name = " ".join(name.split())[:MAX_NAME_LENGTH].strip()
    if not name or not all(character.isprintable() for character in name):
        raise ValueError("Give the Remix a readable name.")
    return name


def _structural_mix(mix) -> dict[str, str]:
    if not isinstance(mix, dict) or set(mix) != set(CHANNELS):
        raise ValueError("A Remix needs exactly one Pak for each of the six components.")
    if any(not isinstance(mix[channel], str) or not _PAK_ID.fullmatch(mix[channel])
           for channel in CHANNELS):
        raise ValueError("Every Remix component needs a valid Pak ID.")
    return {channel: mix[channel] for channel in CHANNELS}


def mix_issues(mix, catalog=None) -> list[str]:
    """Describe unavailable providers without replacing the player's choices."""
    catalog = catalog if catalog is not None else get_catalog()
    try:
        mix = _structural_mix(mix)
    except ValueError as exc:
        return [str(exc)]
    issues = []
    for channel, pak_id in mix.items():
        pak = catalog.by_id.get(pak_id)
        if pak is None:
            issues.append(f"{channel.title()}: missing Pak {pak_id}.")
        elif channel not in pak.parts:
            issues.append(f"{channel.title()}: {pak.name} does not supply this component.")
    return issues


def validate_mix(mix, catalog=None) -> dict[str, str]:
    """Copy a complete installed selection, or explain why it cannot be played."""
    checked = _structural_mix(mix)
    issues = mix_issues(checked, catalog)
    if issues:
        raise ValueError(" ".join(issues))
    return checked


def _record(raw) -> Remix:
    if not isinstance(raw, dict):
        raise ValueError("Invalid saved Remix.")
    identifier = raw.get("id")
    if not isinstance(identifier, str) or not _REMIX_ID.fullmatch(identifier):
        raise ValueError("Invalid saved Remix ID.")
    return Remix(identifier, normalize_name(raw.get("name")), _structural_mix(raw.get("mix")))


class RemixStore:
    def __init__(self, directory: Path | None = None, catalog=None):
        self.catalog = catalog if catalog is not None else get_catalog()
        self.path = (directory if directory is not None else data_root()) / "remixes.json"
        self.error = ""

    def load(self) -> list[Remix]:
        """Keep structurally valid favorites even when a Pak has been removed."""
        self.error = ""
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if (not isinstance(raw, dict) or type(raw.get("schema_version")) is not int
                    or raw["schema_version"] != 1 or not isinstance(raw.get("remixes"), list)):
                raise ValueError("Unsupported saved Remix format.")
            remixes = []
            seen = set()
            skipped = 0
            for item in raw["remixes"]:
                try:
                    remix = _record(item)
                    if remix.id in seen:
                        raise ValueError("Duplicate saved Remix ID.")
                except ValueError:
                    skipped += 1
                    continue
                remixes.append(remix)
                seen.add(remix.id)
            if skipped:
                self.error = f"Skipped {skipped} invalid saved Remix entries."
            return remixes
        except FileNotFoundError:
            return []
        except (OSError, ValueError, TypeError) as exc:
            self.error = f"Could not read saved Remixes: {exc}"
            return []

    def save(self, remixes: list[Remix]) -> bool:
        """Replace the file atomically; report failure without losing its old bytes."""
        temp_path = None
        try:
            records = [_record(asdict(remix)) for remix in remixes]
            if len({remix.id for remix in records}) != len(records):
                raise ValueError("Saved Remix IDs must be unique.")
            payload = {"schema_version": 1, "remixes": [asdict(remix) for remix in records]}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix="remixes-", suffix=".tmp", delete=False) as stream:
                temp_path = Path(stream.name)
                json.dump(payload, stream, indent=2, ensure_ascii=False, allow_nan=False)
                stream.write("\n")
            temp_path.replace(self.path)
            self.error = ""
            return True
        except (OSError, ValueError, TypeError) as exc:
            self.error = f"Could not save Remixes: {exc}"
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
            return False
