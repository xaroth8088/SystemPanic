"""Lazy component-local asset handles. Loading never opens a display or audio device."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pygame


class SoundPlayer(Protocol):
    def play_asset(self, asset: SoundAsset, *, loop: bool = False, volume: float = 1.) -> None: ...
    def stop_asset(self, asset: SoundAsset) -> None: ...


@dataclass(frozen=True)
class SpriteFrame:
    """A rectangle in a spritesheet; pixel coordinates, never simulation state."""
    image: ImageAsset
    rect: tuple[int, int, int, int]


class ImageAsset:
    def __init__(self, path: Path):
        self.path = path
        self._surface = None

    @property
    def surface(self) -> pygame.Surface:
        """Decode lazily; works without a display and retains original alpha."""
        if self._surface is None:
            self._surface = pygame.image.load(self.path)
        return self._surface

    def frame(self, index: int, *, columns: int = 1, rows: int = 1) -> SpriteFrame:
        """Select a row-major frame from an evenly divided spritesheet."""
        if columns < 1 or rows < 1 or not 0 <= index < columns * rows:
            raise ValueError("Invalid spritesheet frame or grid")
        width, height = self.surface.get_size()
        if width % columns or height % rows:
            raise ValueError("Spritesheet dimensions must divide evenly into its grid")
        width, height = width // columns, height // rows
        return SpriteFrame(self, (index % columns * width, index // columns * height, width, height))


class SoundAsset:
    def __init__(self, path: Path, player: SoundPlayer | None = None):
        self.path, self._player = path, player

    def play(self, *, loop: bool = False, volume: float = 1.) -> None:
        """Play through this run's effects bus; a loop is idempotent until stopped."""
        if self._player:
            self._player.play_asset(self, loop=loop, volume=max(0., min(1., volume)))

    def stop(self) -> None:
        if self._player:
            self._player.stop_asset(self)


class AssetLoader:
    def __init__(self, directory: Path, overrides=None, player: SoundPlayer | None = None):
        self.directory = directory.resolve()
        self.overrides = overrides or {}
        self.player = player
        self.handles = {}

    def load(self, filename: str) -> ImageAsset | SoundAsset:
        if not isinstance(filename, str) or not filename or Path(filename).is_absolute():
            raise ValueError("Asset paths must be relative to the component folder")
        # Even overridden names are checked against the provider's directory.
        original = (self.directory / filename).resolve()
        if not original.is_relative_to(self.directory):
            raise ValueError("Asset path escapes its component folder")
        path = self.overrides.get(filename, original)
        if not path.is_file():
            raise ValueError(f"Missing component asset: {filename}")
        if filename not in self.handles:
            if path.suffix.lower() in (".png", ".webp", ".jpg", ".jpeg"):
                handle = ImageAsset(path)
            elif path.suffix.lower() in (".ogg", ".wav"):
                handle = SoundAsset(path, self.player)
            else:
                raise ValueError(f"Unsupported component asset: {filename}")
            self.handles[filename] = handle
        return self.handles[filename]

    def stop_sounds(self) -> None:
        for handle in self.handles.values():
            if isinstance(handle, SoundAsset):
                handle.stop()
