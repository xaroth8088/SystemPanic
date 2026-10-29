# Iron Circuit: obstacles

Read [this Pak's memory](../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py). `obstacle.py` subclasses `ObstaclesBase`. Required: `build(world), sprite(world, entity=None)`. Return fresh Cover objects with explicit health/max_health. Override draw for local style. Geometry helpers return contacts without landing, wrapping or bounce policy.

Load local handles in `init()`; their attribute names are private choices. Instances belong to one run. Use explicit lifecycle callbacks for setup/cleanup. Rendering cannot advance gameplay. The host schedules projectile/effect callbacks once; do not also advance them from the component update. Local helper modules and assets can be copied as partial components. Preserve asset provenance.

Literal closed road lanes include an oval and several chicane/dogleg/kidney circuits. TrackRail capsule geometry stops bodies, never projectiles, and is impervious. Terrain drawing paints asphalt/markings beneath rails. Arrival/provider-change hooks place an off-track pilot on the nearest lane. Seed a private random.Random from world.seed and world.wave; do not consume combat RNG. The host calls build at every level arrival even if this component is locked/solo, and on provider changes. Return fresh full-health objects; leave broad passages/margins.

Renewal TrackRail draws animated local guardrail texture along its six-pixel rail and retains its existing circle/capsule collision and projectile transparency. Cached rotated strips are presentation-only and consume no gameplay RNG.

Renewal: local four-frame horizontal terrain animation. Presentation stays inside the actual collision footprint; sprite selection/drawing cannot mutate simulation.
