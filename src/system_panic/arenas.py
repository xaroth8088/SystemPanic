"""Compatibility lookup; each Pak owns its actual geometry factory."""
from .paks import PAKS

def build_arena(kind):
    return next(pak for pak in PAKS if pak.arena == kind).make_arena()
