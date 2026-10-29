# Vector Coil: obstacles

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Sparse capacitor posts and interrupted rails leave room for angular capture circuits. take_damage returns zero: geometry is impervious even in mixed play, but regenerates each level.

Renewal: local four-frame horizontal terrain animation. Presentation stays inside the actual collision footprint; sprite selection/drawing cannot mutate simulation.
