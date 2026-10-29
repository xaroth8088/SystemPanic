# Neon Breach: enemy

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). Copy this entire role folder as a partial Pak. Actor factories, local helpers, spawn/difficulty/reward policy and contacts belong here. No private sibling-role state or host feature traits.

Brick drones drift and mark a predicted target for .55s before firing. The aim marker is visual only; scaled shots and movement remain enemy-local.

The local four-frame sheet selects poses without changing simulation/RNG. Owned transient cues recreate after world cleanup; death clears them. Use actual shape/body/projectile filters for geometry, with rects only as broad-phase metadata.

## Quiet presentation and tail routing (2026-10-28)

Advance attack/recovery/aim marker objects are removed. Creature animation, target locking, attack timing, movement, vulnerability and damage rules remain local and unchanged. Delayed damage areas are invisible before activation; actual active hazards/projectiles still render. Only creature teleport destination warnings remain elsewhere. This supersedes earlier cue-presentation notes; see the Pak-wide presentation memory.
