"""Small explicit contract for independently interchangeable game components."""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Pak:
    id: str
    name: str
    version: str
    directory: Path
    components: tuple[str, ...]
    subtitle: str
    color: tuple[int, int, int]
    description: str
    sprites: tuple[Path | None, ...]
    music: Path | None = None
    pilot: str = ""
    weapon: str = ""
    enemy: str = ""
    arena: str = ""
    controls: str = ""
    special: str = ""
    move: Callable | None = None
    fire: Callable | None = None
    advance_enemy: Callable | None = None
    make_arena: Callable | None = None
    cooldown: float = .25
    splits: int = 0
    prepare_pilot: Callable | None = None
    draw_arena: Callable | None = None
    demo_controls: Callable | None = None
    pilot_sprite: str = "upright"
    rotate_enemy: bool = False

    @property
    def complete(self):
        return len(self.components) == 4
