"""Public Pak API 4. Paks own rules; the host supplies scheduling and primitives.

Only the documented methods/properties below form the contract. Names used to
store loaded handles, animation timers or other private state are author-owned.
Each world receives fresh instances; draw/sprite/track must not advance gameplay.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from pygame.surface import Surface

from .pak_assets import AssetLoader, ImageAsset, SoundAsset, SoundPlayer, SpriteFrame
from .model import Controls, Cover, Enemy, Pilot, Vec

if TYPE_CHECKING:
    from .world import World
    from .graphics import Graphics

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

    def on_level_start(self, world: World) -> None:
        """New level number/geometry are ready, before initial enemies are spawned."""

    def on_level_complete(self, world: World) -> None:
        """Own level rewards/recovery; called once before the cleared intermission."""

    def on_enemy_destroyed(self, world: World, enemy: Enemy) -> None:
        """Once-only removal notification; never emitted for adoption/despawning.

        The shared kill counter is already updated. Components own any response;
        the host does not prescribe drops, resources, healing or combat rules.
        """

    def on_shuffle(self, world: World, changed: frozenset[str]) -> None:
        """All new components/geometry are ready; own any swap protection/reaction."""

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

    def draw(self, graphics: Graphics, surface: Surface, world: World, *, reduced_motion=False) -> None:
        """Read-only pilot presentation; override for local shape/edge alignment."""
        import pygame
        p=world.player
        if p.invulnerable>0:
            pygame.draw.circle(surface,world.pak('pilot').color,p.pos,20,1)
        if world.phase!='active' or world.transition>0 or p.invulnerable<=0 or int(world.time*12)%2 or reduced_motion:
            image=graphics.component_sprite(world,'pilot',p,44)
            surface.blit(image,image.get_rect(center=p.pos))

    @abstractmethod
    def create(self, world: World, position: Vec) -> Pilot:
        """Create the Pak's pilot body/stats. The host preserves shared state on swaps."""

    @abstractmethod
    def update(self, world: World, dt: float, control: Controls) -> None:
        """Own movement, input edges, abilities and their private timing/state."""

    def aim_direction(self, world: World) -> Vec | None:
        """Optional explicit firing direction for weapons to respect; None leaves them free.

        This query must not advance state. The pilot owns its intent; each weapon
        chooses how to use it. No host targeting policy is implied.
        """
        return None

    def status(self, world: World) -> str:
        """Optional live pilot-state hint for either input device; never advance state."""
        return ""

    def on_contact(self, world: World, enemy: Enemy, dt: float) -> None:
        """Optional response to overlapping an enemy; no built-in ram/dash behavior."""

    def take_damage(self, world: World, damage: float) -> float:
        """Override for shields, recovery, feedback, etc.; default applies raw damage."""
        return world.apply_damage(world.player, damage)

    def on_death(self, world: World) -> None:
        """Optional pilot defeat effects. The host does not prescribe a death burst."""

    def demo_controls(self, world: World) -> Controls | None:
        """Optional ordinary-input policy used only by the QA/demo runner."""
        return None


class EnemyBase(SpriteComponent):
    def draw(self, graphics: Graphics, surface: Surface, world: World, enemy: Enemy, *, reduced_motion=False) -> None:
        """Read-only body presentation; default retains centered sprite rendering."""
        image=graphics.component_sprite(world,'enemy',enemy,int(enemy.radius*3.4),rotate=not reduced_motion)
        surface.blit(image,image.get_rect(center=enemy.pos))

    @abstractmethod
    def spawn_position(self, world: World) -> Vec:
        """Choose an initial enemy position, including any distance/safety policy."""

    @abstractmethod
    def create(self, world: World, identity: int, position: Vec) -> Enemy:
        """Own spawn stats/state. Return this identity, including on component adoption."""

    @abstractmethod
    def advance_enemy(self, world: World, enemy: Enemy, dt: float) -> None:
        """Own each enemy's AI and clocks. The host only schedules this call."""

    def on_contact(self, world: World, enemy: Enemy, dt: float) -> None:
        """Optional contact behavior; the host assigns no contact damage."""

    def take_damage(self, world: World, enemy: Enemy, damage: float) -> float:
        return world.apply_damage(enemy, damage)

    def on_death(self, world: World, enemy: Enemy) -> None:
        """Own rewards, effects and child spawns. Called once, after removal."""


class WeaponBase(SpriteComponent):
    def demo_controls(self, world: World, controls: Controls) -> Controls:
        """Optionally refine ordinary QA input for a weapon's local interaction.

        The input is the pilot's demo policy. This is never used for live input.
        """
        return controls

    def create_powerup(self, world: World, position: Vec) -> PowerupBase | None:
        """Factory called at every tenth kill; the returned Pak object owns its behavior."""
        return None

    def on_powerup(self, world: World, count: int) -> None:
        """Optional pickup feedback. world.powerups_collected persists across swaps."""

    @abstractmethod
    def update(self, world: World, dt: float, control: Controls) -> None:
        """Own triggering/cadence/charges. Append Pak-owned projectiles or effects."""


class ProjectileBase(ABC):
    """A scheduled object, not a menu of built-in weapon features."""
    def __init__(self, position: Vec, velocity: Vec, radius: float = 4.):
        self.pos, self.vel = Vec(position), Vec(velocity)
        self.radius, self.alive = radius, True

    @abstractmethod
    def update(self, world: World, dt: float) -> None:
        """Own motion, lifetime and every collision outcome. Set alive=False to remove."""

    @abstractmethod
    def draw(self, graphics: Graphics, surface: Surface, world: World) -> None:
        """Own projectile presentation. Never mutate simulation here."""

    def is_threat_to(self, world: World, body: object) -> bool:
        """Optional query for Pak demo AI; the host never infers a projectile team."""
        return False


class EffectBase(ABC):
    """A visual-only transient. Gameplay rules belong in active component updates."""
    alive: bool = True

    @abstractmethod
    def update(self, dt: float) -> None: ...

    @abstractmethod
    def draw(self, graphics: Graphics, surface: Surface, world: World) -> None: ...


class PowerupBase(ABC):
    """Pak-owned collectible; the host only spawns, schedules and counts collections."""
    def __init__(self, position: Vec, radius: float = 10.):
        self.pos, self.vel = Vec(position), Vec()
        self.radius, self.alive = radius, True

    @abstractmethod
    def update(self, world: World, dt: float) -> None:
        """Own motion, lifetime and pickup conditions; call world.collect_powerup(self)."""

    @abstractmethod
    def draw(self, graphics: Graphics, surface: Surface, world: World) -> None:
        """Read-only presentation, using captured local asset handles."""


class MusicBase(ComponentBase):
    @abstractmethod
    def track(self, world: World | None = None) -> SoundAsset | None:
        """Return the current track, or None for silence. The engine owns playback."""


class BackgroundBase(ComponentBase):
    @abstractmethod
    def draw(self, surface: Surface, world: World) -> None:
        """Draw scenery behind entities without mutating world state or RNG."""


class ObstaclesBase(SpriteComponent):
    def update(self, world: World, dt: float) -> None:
        """Optional active-step hazards/dynamic geometry, entirely Pak-owned."""

    def draw_floor(self, graphics: Graphics, surface: Surface, world: World) -> None:
        """Optional read-only terrain presentation underneath obstacle bodies."""

    @abstractmethod
    def build(self, world: World) -> list[Cover]:
        """Fresh geometry each level/provider change; use seed/wave for procedural rules.

        Called after wave increments, before actor placement. Keep generation bounded;
        [] is valid. A private seeded RNG keeps layouts independent of combat history.
        """

    def take_damage(self, world: World, obstacle: Cover, damage: float) -> float:
        """Own obstacle durability. Override to return zero for impervious geometry.

        The default preserves raw-damage behavior for existing API 4 components.
        Attackers call world.hit_cover rather than writing obstacle health.
        """
        applied = min(max(0., obstacle.health), max(0., damage))
        obstacle.health -= applied
        return applied

    def draw(self, graphics: Graphics, surface: Surface, world: World, obstacle: Cover) -> None:
        """Default generic obstacle presentation; override for a Pak's own style."""
        graphics.draw_obstacle(surface, world, obstacle)


__all__ = ["ComponentBase", "PilotBase", "EnemyBase", "WeaponBase", "MusicBase", "BackgroundBase", "ObstaclesBase",
           "ProjectileBase", "EffectBase", "PowerupBase", "ImageAsset", "SoundAsset", "SpriteFrame", "Sprite"]
