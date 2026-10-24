from .model import Pak
from . import signal_runner, void_drifter, iron_circuit, sky_forge, phase_garden, orbit_keeper

PAKS: tuple[Pak, ...] = tuple(module.PAK for module in (
    signal_runner, void_drifter, iron_circuit, sky_forge, phase_garden, orbit_keeper
))
BY_ID = {pak.id: pak for pak in PAKS}
CHANNELS = ("pilot", "weapon", "enemy", "arena")


def validate_registry():
    if len(BY_ID) != len(PAKS):
        raise ValueError("Duplicate Pak ID")
    for pak in PAKS:
        if not all(callable(getattr(pak, behavior)) for behavior in ("move", "fire", "advance_enemy", "make_arena")):
            raise ValueError(f"Incomplete Pak: {pak.id}")
    for channel in CHANNELS:
        if len({getattr(pak, channel) for pak in PAKS}) != len(PAKS):
            raise ValueError(f"Launch Paks must have distinct {channel} behaviors")
    return True


validate_registry()
