# Vector Coil: enemy

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). Copy this entire role folder as a partial Pak. Actor factories, local helpers, spawn/difficulty/reward policy and contacts belong here. No private sibling-role state or host feature traits.

Sparks retain level-scaled movement, periodic pursuit turns and real shape/border reflections. Capture and trail damage remain the weapon role, never a pilot passive or host rule.

The local four-frame sheet selects poses without changing simulation/RNG. Owned transient cues recreate after world cleanup; death clears them. Use actual shape/body/projectile filters for geometry, with rects only as broad-phase metadata.

## Arcade feedback (2026-10-26)

Contact damage is now (32+1.3*(wave-1)^.7)*difficulty. Drift periods of 1.3-2.7s lead to a stationary 0.25-0.45s pause, followed by a 0.4s dart at 3.8x ordinary move_speed. Dart heading is sampled uniformly from the run RNG, independent of player position. Actual geometry/border normals still reflect velocity. No host AI state or new telegraph object is used.
