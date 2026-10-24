"""Immutable discovered definitions; mutable component instances belong to a run."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping
from ..pak_api import ComponentBase

CHANNELS = ("pilot", "enemy", "weapon", "music", "background", "obstacles")
GAMEPLAY_CHANNELS = ("pilot", "enemy", "weapon", "obstacles")


@dataclass(frozen=True)
class ComponentSpec:
    implementation: type[ComponentBase]
    directory: Path
    overrides: Mapping[str, Path] = field(default_factory=dict)

    def create(self, audio=None) -> ComponentBase:
        return self.implementation(self.directory, overrides=self.overrides, audio=audio)


@dataclass(frozen=True)
class Pak:
    id: str
    name: str
    version: str
    directory: Path
    subtitle: str
    color: tuple[int, int, int]
    description: str
    parts: Mapping[str, ComponentSpec]

    @property
    def components(self):
        return tuple(c for c in CHANNELS if c in self.parts)

    def create(self, channel, audio=None):
        return self.parts[channel].create(audio)

    @property
    def complete(self):
        return all(c in self.parts for c in CHANNELS)
