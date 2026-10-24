"""Legacy helper; new code uses world.component('obstacles').build()."""
from .paks import get_catalog

def build_arena(pak_id, catalog=None):
    catalog = catalog if catalog is not None else get_catalog()
    return catalog.by_id[pak_id].create("obstacles").build()
