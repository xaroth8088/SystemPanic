# Orbit Keeper: weapon

Read [this Pak's memory](../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py). `weapon.py` subclasses `WeaponBase`. Required: `update(world, dt, control), sprite(world, entity=None)`. Own triggering, cadence, charging and firing. Projectile helpers implement their own update/draw, lifetime and hit outcomes; the host does not inspect weapon stats or feature flags.

Load local handles in `init()`; their attribute names are private choices. Instances belong to one run. Use explicit lifecycle callbacks for setup/cleanup. Rendering cannot advance gameplay. The host schedules projectile/effect callbacks once; do not also advance them from the component update. Local helper modules and assets can be copied as partial components. Preserve asset provenance.

aim(world) selects this weapon's assisted/facing direction locally. The host provides no aiming method or firing gate.

Use pilot aim_direction before assistance. Outbound speed is 600 so constrained pilots and radial fire reach distant targets; the .55-second return behavior stays local. Do not silently home outgoing shots away from explicit pilot intent.

Obstacle contacts call world.hit_cover; the selected obstacle component owns durability, including impervious geometry.

Powerups: OrbitKeeperPowerup orbits a slowly approaching center. Glaives do not expire at viewport edges: they turn home after their local outbound timer. Damage 28+5n, launch speed 600+min(160,20n), outbound .55+min(.25,.025n). Each weapon owns its powerup.py subclass, captures local handles, and uses the shared run count; the engine owns only tenth-kill spawning/counting.
