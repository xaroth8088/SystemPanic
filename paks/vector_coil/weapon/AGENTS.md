# Vector Coil: weapon

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

This weapon draws from actual pilot positions while Fire is held; there is no separate cursor. Release clears the tail. A horizontal-only pilot can create an ineffective mix; that is intentional until a swap.

tail.py owns segment intersections, polygon area/containment and one visual effect. A valid loop has at least 900 pixels of area and fully contains enemy circles. Only a newly closed loop applies lethal damage through world.hit_enemy; open tails, contact, straight retracing and mere bounding-box inclusion do nothing. Collinear compression and 512-vertex/6000-length bounds limit memory. Teleports over 160 pixels reset; level changes, swaps and component removal clear private geometry. Drawing never mutates simulation.
