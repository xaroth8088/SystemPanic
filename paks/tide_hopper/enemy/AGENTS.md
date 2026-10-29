# Tide Hopper: enemy

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). Copy this entire role folder as a partial Pak. Actor factories, local helpers, spawn/difficulty/reward policy and contacts belong here. No private sibling-role state or host feature traits.

Traffic now hops between the same 24+48k centers as the pilot and pauses visibly between steps. Normal pilot hops span one cell; the protected ferry hop spans two (96px). Later traffic changes rows on this lattice. Public positional displacement from a foreign weapon cancels the current route and yields briefly; sustained harpoon towing is never snapped back. After release traffic travels to a clear node through collision checks. No sibling-private capture flag is read.

The local four-frame sheet selects poses without changing simulation/RNG. Owned transient cues recreate after world cleanup; death clears them. Use actual shape/body/projectile filters for geometry, with rects only as broad-phase metadata.
