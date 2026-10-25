# Neon Breach: weapon

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Prefer a non-None pilot aim_direction over ordinary assistance. Keep aiming and any projectile guidance in this component; the host only schedules it.

Up to two accelerating plasma pinballs reflect from bounds/cover/targets/paddle. Guidance uses bounded angular turn rate, including a 180-degree reversal. Prune ball references against world.projectiles after host cleanup.

Obstacle contacts call world.hit_cover; the selected obstacle component owns durability, including impervious geometry.
