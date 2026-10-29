# Sky Forge: enemy

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). Copy this entire role folder as a partial Pak. Actor factories, local helpers, spawn/difficulty/reward policy and contacts belong here. No private sibling-role state or host feature traits.

Crawlers have gravity and flat-foot landings, .38s leap windup, locked jump velocity, and .48s harmless recovery. Lower targets cause committed walks off deck edges. A high pilot triggers a marked .85s/.3s rooftop heat zone that hits once. Local physics/cues/hazards are copied with this enemy folder.

The local four-frame sheet selects poses without changing simulation/RNG. Owned transient cues recreate after world cleanup; death clears them. Use actual shape/body/projectile filters for geometry, with rects only as broad-phase metadata.

## Arcade feedback (2026-10-26)

Crawler physics shares the true 480px floor boundary. Its own read-only draw override aligns each animation pose's significant-alpha feet to body.pos.y+body.radius; default enemy rendering remains centered. This corrects transparent frame margins without changing collision radii or introducing host crawler rules.

## Quiet presentation and tail routing (2026-10-28)

Advance attack/recovery/aim marker objects are removed. Creature animation, target locking, attack timing, movement, vulnerability and damage rules remain local and unchanged. Delayed damage areas are invisible before activation; actual active hazards/projectiles still render. Only creature teleport destination warnings remain elsewhere. This supersedes earlier cue-presentation notes; see the Pak-wide presentation memory.
