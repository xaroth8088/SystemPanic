# Iron Circuit: weapon

Read [this Pak's memory](../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py). `weapon.py` subclasses `WeaponBase`. Required: `update(world, dt, control), sprite(world, entity=None)`. Own triggering, cadence, charging and firing. Projectile helpers implement their own update/draw, lifetime and hit outcomes; the host does not inspect weapon stats or feature flags.

Load local handles in `init()`; their attribute names are private choices. Instances belong to one run. Use explicit lifecycle callbacks for setup/cleanup. Rendering cannot advance gameplay. The host schedules projectile/effect callbacks once; do not also advance them from the component update. Local helper modules and assets can be copied as partial components. Preserve asset provenance.

aim(world) selects this weapon's assisted/facing direction locally. The host provides no aiming method or firing gate.
