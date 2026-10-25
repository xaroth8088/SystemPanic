# Maze Muncher: weapon

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Prefer a non-None pilot aim_direction over ordinary assistance. Keep aiming and any projectile guidance in this component; the host only schedules it.

Normal fire is now a forward contact dash with mutual knockback; see the current formula below. No wave or projectile is launched.

Powerups: MazeMuncherPowerup is a stationary power pellet. Normal attacks are short forward lunges, not waves/projectiles: 460 px/s for .14+min(.08,.008n) seconds, 20+5n damage, recovery max(.3,.62/(1+.035n)). One swept hit knocks both bodies apart and ends the lunge. The pilot retains its energized contact special. Each weapon owns its powerup.py subclass, captures local handles, and uses the shared run count; the engine owns only tenth-kill spawning/counting.
