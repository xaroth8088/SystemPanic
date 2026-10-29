# Void Drifter: obstacles

Read [this Pak's memory](../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py). `obstacle.py` subclasses `ObstaclesBase`. Required: `build(world), sprite(world, entity=None)`. Return fresh Cover objects with explicit health/max_health. Override draw for local style. Geometry helpers return contacts without landing, wrapping or bounce policy.

Load local handles in `init()`; their attribute names are private choices. Instances belong to one run. Use explicit lifecycle callbacks for setup/cleanup. Rendering cannot advance gameplay. The host schedules projectile/effect callbacks once; do not also advance them from the component update. Local helper modules and assets can be copied as partial components. Preserve asset provenance.

Seeded space-rock islands surround a nonblocking black hole. Its active update attracts nearby pilot/enemy bodies, shots and collectibles independently of their own motion, with damage near the horizon. Scheduled comets cross the viewport and leave cleanly; their collision/feedback/drawing stay local. Seed a private random.Random from world.seed and world.wave; do not consume combat RNG. The host calls build at every level arrival even if this component is locked/solo, and on provider changes. Return fresh full-health objects; leave broad passages/margins.

Renewal: local four-frame horizontal terrain animation. Presentation stays inside the actual collision footprint; sprite selection/drawing cannot mutate simulation.

Playtest refinement: influence radius 170; both attraction terms use (1-distance/170)². Maximum positional drift is 10 px/s and acceleration 75 px/s², decisively below this pilot’s 360 px/s² thrust. Ordinary outward thrust escapes from the center and horizon in focused tests. Inner-horizon damage and nonblocking geometry remain local.

## Procedural space presentation (2026-10-28)
visuals.py owns cached antialiased procedural effect frames: a tilted glowing accretion disk, bent-light arc, dark horizon and orbiting dust for the well; tapered layered ion plumes, streaks and faceted icy heads for comets. Cache limits are 36 well frames and 24 comet frames. Selection reads simulation time/age only; reduced motion holds decorative animation at frame zero while hazards still move normally. Comet rotation preserves its head at the physical center for every direction. Gravity, hit radii, movement/spawn/damage and RNG are unchanged. No bitmap asset generation, file writes or generation dependencies occur at runtime; these are ordinary vector drawing caches.
