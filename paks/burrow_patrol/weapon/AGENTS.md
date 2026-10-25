# Burrow Patrol: weapon

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Prefer a non-None pilot aim_direction over ordinary assistance. Keep aiming and any projectile guidance in this component; the host only schedules it.

A held pressure tether maintains target identity, pumps gradual damage and pops after sufficient pressure. Misses still draw a pressure stream. PressureLine is visual-only; targeting/damage stays in the weapon update.

Obstacle contacts call world.hit_cover; the selected obstacle component owns durability, including impervious geometry.

Powerups: BurrowPatrolPowerup digs toward the pilot in discrete steps. Tether reach is min(300,145+18n); out-of-range targets cannot take damage or keep a target lock. Pressure grows at .85+.08n and gradual damage is 7+2n per second. Miss visuals end at the same reach. Each weapon owns its powerup.py subclass, captures local handles, and uses the shared run count; the engine owns only tenth-kill spawning/counting.
