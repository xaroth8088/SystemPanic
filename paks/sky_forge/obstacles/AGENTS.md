# Sky Forge: obstacles

Read [this Pak's memory](../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py). `obstacle.py` subclasses `ObstaclesBase`. Required: `build(world), sprite(world, entity=None)`. Return fresh Cover objects with explicit health/max_health. Override draw for local style. Geometry helpers return contacts without landing, wrapping or bounce policy.

Load local handles in `init()`; their attribute names are private choices. Instances belong to one run. Use explicit lifecycle callbacks for setup/cleanup. Rendering cannot advance gameplay. The host schedules projectile/effect callbacks once; do not also advance them from the component update. Local helper modules and assets can be copied as partial components. Preserve asset provenance.

Staggered decks with bounded spacing for double jumps. Seed a private random.Random from world.seed and world.wave; do not consume combat RNG. The host calls build at every level arrival even if this component is locked/solo, and on provider changes. Return fresh full-health objects; leave broad passages/margins.
