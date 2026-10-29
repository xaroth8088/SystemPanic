"""Exact provider exclusions, bounded selection and local performance history."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import tempfile

from .paks import CHANNELS
from .remixes import structural_mix


def mix_key(mix):
    return tuple(mix[channel] for channel in CHANNELS)


class NoAvailableCombination(ValueError):
    pass


class CombinationSpace:
    """Select without rejection loops or enumerating the provider Cartesian product."""
    def __init__(self, pools):
        self.pools = [tuple(pool) for pool in pools]
        self.total = math.prod(map(len, self.pools))

    def rank(self, key):
        rank = 0
        for pool, value in zip(self.pools, key):
            if value not in pool:
                return None
            rank = rank * len(pool) + pool.index(value)
        return rank

    def excluded_ranks(self, excluded):
        return sorted({rank for key in excluded if (rank := self.rank(key)) is not None})

    def available(self, excluded):
        return self.total - len(self.excluded_ranks(excluded))

    def pick(self, rng, excluded):
        blocked = self.excluded_ranks(excluded)
        remaining = self.total - len(blocked)
        if remaining <= 0:
            return None
        rank = rng.randrange(remaining)
        for skipped in blocked:
            if skipped > rank:
                break
            rank += 1
        values = []
        for pool in reversed(self.pools):
            rank, index = divmod(rank, len(pool))
            values.append(pool[index])
        return dict(zip(CHANNELS, reversed(values)))


@dataclass
class FlaggedCombination:
    mix: dict[str, str]
    detected_at: str
    fps: float
    seconds: float


def _record(raw):
    if not isinstance(raw, dict):
        raise ValueError("Invalid combination record")
    mix = structural_mix(raw.get("mix"))
    stamp = raw.get("detected_at")
    if not isinstance(stamp, str) or len(stamp) > 40:
        raise ValueError("Invalid detection date")
    date = datetime.fromisoformat(stamp)
    if date.tzinfo is None:
        raise ValueError("Detection date needs a timezone")
    stamp = date.astimezone(timezone.utc).isoformat(timespec="seconds")
    values = [raw.get(name) for name in ("fps", "seconds")]
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Invalid performance measurement")
    return FlaggedCombination(mix, stamp, *values)


class CombinationHistory:
    def __init__(self, directory: Path):
        self.path = directory / "blocked_combinations.json"
        self.entries = []
        self.keys = set()
        self.error = ""
        self.dirty = False
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if (not isinstance(raw, dict) or type(raw.get("schema_version")) is not int
                    or raw["schema_version"] != 1 or not isinstance(raw.get("combinations"), list)):
                raise ValueError("Unsupported combination history format")
            skipped = 0
            for item in raw["combinations"]:
                try:
                    entry = _record(item)
                except (ValueError, TypeError, OverflowError):
                    skipped += 1
                    continue
                key = mix_key(entry.mix)
                if key not in self.keys:
                    self.entries.append(entry)
                    self.keys.add(key)
            if skipped:
                self.error = f"Skipped {skipped} invalid flagged combinations."
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError) as exc:
            self.error = f"Could not read flagged combinations: {exc}"

    def _save(self, entries):
        temporary = None
        try:
            payload = {"schema_version": 1, "combinations": [asdict(_record(asdict(item))) for item in entries]}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix="combinations-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(payload, stream, indent=2, allow_nan=False)
                stream.write("\n")
            temporary.replace(self.path)
            self.error = ""
            return True
        except (OSError, ValueError, TypeError) as exc:
            self.error = f"Could not save flagged combinations: {exc}"
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
            return False

    def flag(self, mix, fps, seconds):
        checked = structural_mix(mix)
        if mix_key(checked) not in self.keys:
            self.entries.append(_record({"mix": checked, "detected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                          "fps": fps, "seconds": seconds}))
            self.keys.add(mix_key(checked))
        # Always exclude in memory, even if disk writes are temporarily unavailable.
        self.dirty = True
        return self.retry()

    def retry(self):
        self.dirty = not self._save(self.entries)
        return not self.dirty

    def remove(self, key):
        remaining = [entry for entry in self.entries if mix_key(entry.mix) != key]
        if not self._save(remaining):
            return False
        self.entries = remaining
        self.keys.discard(key)
        self.dirty = False
        return True


class PerformanceWatch:
    """Consecutive slow presented frames, using unclamped wall time."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.context = None
        self.seconds = 0.
        self.frames = 0
        self.fps = 0.

    def observe(self, elapsed, context):
        if context is None or not math.isfinite(elapsed) or elapsed <= 0:
            self.reset()
            return False
        if context != self.context:
            self.reset()
            self.context = context
        self.fps = 1 / elapsed
        if elapsed <= .1:  # Exactly 10 FPS is healthy.
            self.seconds = 0.
            self.frames = 0
            return False
        self.seconds += elapsed
        self.frames += 1
        return self.seconds > 1.0

    @property
    def slow_fps(self):
        return self.frames / self.seconds if self.seconds else 0.
