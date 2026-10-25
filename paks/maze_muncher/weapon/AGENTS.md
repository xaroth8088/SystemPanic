# Maze Muncher: weapon

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Prefer a non-None pilot aim_direction over ordinary assistance. Keep aiming and any projectile guidance in this component; the host only schedules it.

Normal fire emits a short 70-pixel directional bite for 16 damage, at most once to one target per bite, every .48 seconds. Solid cover blocks its line of sight. The .16-second visual expires and cannot damage again; no screen-wide waves or wall damage. The pilot retains its energized contact special.
