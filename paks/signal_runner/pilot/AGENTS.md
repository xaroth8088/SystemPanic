# Signal Runner: pilot

Read [this Pak's memory](../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py). `pilot.py` subclasses `PilotBase`. Required: `create(world, position), update(world, dt, control), sprite(world, entity=None)`. Own body stats, raw input edges, ability timers, locomotion and take_damage/on_contact behavior. Jump/orbit/dash state stays here, never in core models.

Load local handles in `init()`; their attribute names are private choices. Instances belong to one run. Use explicit lifecycle callbacks for setup/cleanup. Rendering cannot advance gameplay. The host schedules projectile/effect callbacks once; do not also advance them from the component update. Local helper modules and assets can be copied as partial components. Preserve asset provenance.
