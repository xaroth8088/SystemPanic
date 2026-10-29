# Burrow Patrol: enemy

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). Copy this entire role folder as a partial Pak. Actor factories, local helpers, spawn/difficulty/reward policy and contacts belong here. No private sibling-role state or host feature traits.

Worms hunt, burrow through terrain for .9s with .65 damage armor, safely emerge for .55s, then rush a locked target for .55s. Burrow/emerge contacts are harmless. Safe-position emergence and all cue/phase rules stay here.

The local four-frame sheet selects poses without changing simulation/RNG. Owned transient cues recreate after world cleanup; death clears them. Use actual shape/body/projectile filters for geometry, with rects only as broad-phase metadata.

## Arcade feedback (2026-10-26)

No WormCue or emerge windup is emitted. After the 0.9s underground phase, choose a safe emergence position and immediately rush the locked target for 0.55s. Burrow contacts remain harmless; emerging rush contacts deal normal damage immediately. There is no separate emerge state or cue lifetime.
