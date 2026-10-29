# Void Drifter: enemy

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). Copy this entire role folder as a partial Pak. Actor factories, local helpers, spawn/difficulty/reward policy and contacts belong here. No private sibling-role state or host feature traits.

Asteroid fracture families, local spawn/reward policy, drift, gravity and comet interactions remain independently owned. New local frames animate the rock states; no family trait is interpreted by the host.

The local four-frame sheet selects poses without changing simulation/RNG. Owned transient cues recreate after world cleanup; death clears them. Use actual shape/body/projectile filters for geometry, with rects only as broad-phase metadata.
