# Star Bastion: weapon

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Prefer a non-None pilot aim_direction over ordinary assistance. Keep aiming and any projectile guidance in this component; the host only schedules it.

Twin salvo bolts optionally guide, wrap once, damage cover/targets and expire locally. Explicit pilot direction disables guidance; side offsets are perpendicular to the selected firing vector.

Obstacle contacts call world.hit_cover; the selected obstacle component owns durability, including impervious geometry.

Powerups: StarBastionPowerup falls through bunkers toward the bottom lane. Bolts expire outside the viewport; there is no screen wrap. Damage 23+4n and 2+min(4,floor(n/3)) bolts; the original pair stays in the salvo as extras are added. Each weapon owns its powerup.py subclass, captures local handles, and uses the shared run count; the engine owns only tenth-kill spawning/counting.
