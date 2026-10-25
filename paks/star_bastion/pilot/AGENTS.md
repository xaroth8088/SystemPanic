# Star Bastion: pilot

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Movement is strictly horizontal at y = HEIGHT - 24. Create starts at the bottom; level/shuffle hooks relocate along that same lane if mixed cover overlaps. Vertical input is ignored, including during the faster barrel roll. Geometry search and roll timing belong to this pilot.
