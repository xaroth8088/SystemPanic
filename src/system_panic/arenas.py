"""Compatibility lookup; each Pak owns its actual geometry factory."""
from .paks import get_catalog

def build_arena(kind, catalog=None):
    catalog = catalog if catalog is not None else get_catalog()
    return next(pak for pak in catalog.paks if "arena" in pak.components and pak.arena == kind).make_arena()
