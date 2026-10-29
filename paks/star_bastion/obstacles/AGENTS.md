# Star Bastion: obstacles

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Three bunker arches have broad entrances and leave the upper formation field open.

Renewal: local four-frame horizontal terrain animation. Presentation stays inside the actual collision footprint; sprite selection/drawing cannot mutate simulation.

Playtest refinement: each seeded bunker is a 7–9 column, four-row arch made of independent 16px cells with 18 health. Actual shots damage only their first filtered contact; hostile shots also call hit_cover before expiring. Cell drawing shows cracks and chipped gaps without a host bunker rule.
