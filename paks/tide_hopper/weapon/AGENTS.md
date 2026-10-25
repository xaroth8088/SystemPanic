# Tide Hopper: weapon

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Prefer a non-None pilot aim_direction over ordinary assistance. Keep aiming and any projectile guidance in this component; the host only schedules it.

One harpoon catches, reels and finishes a target, then can launch again. Missing/removed targets and host projectile cleanup must release the weapon reference. Tether drawing does not move targets.

Obstacle contacts call world.hit_cover; the selected obstacle component owns durability, including impervious geometry.

Powerups: TideHopperPowerup drifts across a river lane. Hook damage 18+4n, finishing damage 38+8n, reel rate 4+.4n; flight/reeling remain projectile-owned. Each weapon owns its powerup.py subclass, captures local handles, and uses the shared run count; the engine owns only tenth-kill spawning/counting.
