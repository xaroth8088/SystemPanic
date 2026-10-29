# Tide Hopper: obstacles

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Alternating canal islands leave continuous broad crossing lanes.

Renewal: local four-frame horizontal terrain animation. Presentation stays inside the actual collision footprint; sprite selection/drawing cannot mutate simulation.

Playtest refinement: separate seeded island clusters and timber quays occupy lattice cells, leaving two broad crossing canals and north/south routes. Each strip has 90 health and local stone, reeds, timber and damage rendering. The independent background adds moonlit banks, flowing eddies, subtle cell marks and lily pads without reading obstacle-private state.
