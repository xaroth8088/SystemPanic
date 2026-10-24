"""Small explicit contract for independently interchangeable game components."""
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Pak:
    id: str
    name: str
    subtitle: str
    color: tuple[int, int, int]
    pilot: str
    weapon: str
    enemy: str
    arena: str
    controls: str
    special: str
    description: str
    atlas_column: int
    move: Callable | None = None
    fire: Callable | None = None
    advance_enemy: Callable | None = None
    make_arena: Callable | None = None
    cooldown: float = .25
    splits: int = 0
