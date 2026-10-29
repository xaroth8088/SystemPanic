# Phase Garden: background

Read [this Pak's memory](../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py). `background.py` subclasses `BackgroundBase`. Required: `draw(surface, world)`. Own scenery; do not change gameplay state, geometry or RNG while rendering.

Load local handles in `init()`; their attribute names are private choices. Instances belong to one run. Use explicit lifecycle callbacks for setup/cleanup. Rendering cannot advance gameplay. The host schedules projectile/effect callbacks once; do not also advance them from the component update. Local helper modules and assets can be copied as partial components. Preserve asset provenance.

Renewal: local source-derived scenery plus Pak-owned time-based decoration. Drawing is read-only and consumes no gameplay RNG.
