"""Public Pak API 2. Subclass one ABC per component; keep assets beside its code.

Only the documented methods/properties below form the contract. Names used to
store loaded handles, animation timers or other private state are author-owned.
Each world receives fresh instances; draw/sprite/track must not advance gameplay.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
import math
from pathlib import Path
from typing import TYPE_CHECKING

from pygame.surface import Surface

from .pak_assets import AssetLoader, ImageAsset, SoundAsset, SoundPlayer, SpriteFrame
from .model import Controls, Cover, Enemy, Projectile, Vec

if TYPE_CHECKING:
    from .world import World

Sprite = ImageAsset | SpriteFrame | None


class ComponentBase(ABC):
    def __init__(self, directory: Path, *, overrides=None, audio: SoundPlayer | None = None):
        self._assets = AssetLoader(directory, overrides, audio)
        self.init()

    def init(self) -> None:
        """Load component-local handles and initialize private state; no world yet."""

    def load_asset(self, filename: str) -> ImageAsset | SoundAsset:
        """Resolve a local filename, including asset-only Pak overrides."""
        return self._assets.load(filename)

    def activate(self, world: World) -> None:
        """Called when this component enters a run, after clean state is available."""

    def deactivate(self, world: World) -> None:
        """Called before replacement/end of run; the engine also stops owned sounds."""

    def suspend(self) -> None:
        """Stop owned voices on pause, focus loss, transitions or defeat."""
        self._assets.stop_sounds()

    def preview(self) -> Sprite:
        """Optional library thumbnail. It must not require an active world."""
        return None


class SpriteComponent(ComponentBase):
    @abstractmethod
    def sprite(self, world: World | None, entity: object | None = None) -> Sprite:
        """Return a handle/frame for the current state; do not advance simulation."""

    def preview(self) -> Sprite:
        return self.sprite(None)

    def sprite_angle(self, world: World, entity: object) -> float:
        """Optional rotation in degrees, applied by the renderer."""
        return 0.

    def sprite_flip_x(self, world: World, entity: object) -> bool:
        return False


class PilotBase(SpriteComponent):
    controls: str = "Arrows / WASD: move"
    special: str = "X: special"

    @abstractmethod
    def move(self, world: World, dt: float, control: Controls, jump: bool, special: bool) -> None:
        """Advance the pilot using engine-owned state and world.move_body."""

    def demo_controls(self, world: World) -> Controls | None:
        """Optional ordinary-input policy used only by the QA/demo runner."""
        return None


class EnemyBase(SpriteComponent):
    family: str = "enemy"
    splits: int = 0

    @abstractmethod
    def advance_enemy(self, world: World, enemy: Enemy, dt: float) -> None:
        """Advance one enemy; the engine already advances its age and timer."""


class WeaponBase(SpriteComponent):
    cooldown: float = .25

    @abstractmethod
    def fire(self, world: World, direction: Vec) -> None:
        """Create shots/beams using engine combat helpers."""

    def sprite_angle(self, world: World, entity: object) -> float:
        return -math.degrees(math.atan2(entity.vel.y, entity.vel.x)) if isinstance(entity, Projectile) else 0.


class MusicBase(ComponentBase):
    @abstractmethod
    def track(self, world: World | None = None) -> SoundAsset | None:
        """Return the current track, or None for silence. The engine owns playback."""


class BackgroundBase(ComponentBase):
    @abstractmethod
    def draw(self, surface: Surface, world: World) -> None:
        """Draw scenery behind entities without mutating world state or RNG."""


class ObstaclesBase(SpriteComponent):
    @abstractmethod
    def build(self) -> list[Cover]:
        """Return fresh destructible collision geometry; [] is a valid open field."""


__all__ = ["ComponentBase", "PilotBase", "EnemyBase", "WeaponBase", "MusicBase", "BackgroundBase", "ObstaclesBase",
           "ImageAsset", "SoundAsset", "SpriteFrame", "Sprite"]
