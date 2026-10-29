# Phase Garden: enemy

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). Copy this entire role folder as a partial Pak. Actor factories, local helpers, spawn/difficulty/reward policy and contacts belong here. No private sibling-role state or host feature traits.

Phantoms mark a safe destination and predicted target for .6s, relocate, shoot at the locked target from the new origin, and expose for 1.15s. Damage multipliers drift .45, mark .9, exposed 1.4. Marks are harmless contacts; cue drawing never changes state.

The local four-frame sheet selects poses without changing simulation/RNG. Owned transient cues recreate after world cleanup; death clears them. Use actual shape/body/projectile filters for geometry, with rects only as broad-phase metadata.

## Quiet presentation and tail routing (2026-10-28)

RuneCue draws only the circle at the imminent teleport destination while state is mark. Aim rays and the exposed/recovery ring are removed; the locked shot, teleport timing and vulnerability formulas are unchanged.
