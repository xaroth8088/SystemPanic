# Star Bastion: enemy

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). Copy this entire role folder as a partial Pak. Actor factories, local helpers, spawn/difficulty/reward policy and contacts belong here. No private sibling-role state or host feature traits.

Formation armor x.5, dive exposure x1.6, return x1.25. When the attack timer expires it shoots immediately, with no tell/marker state. From level four it also commits to a 1.15s dive, followed by recovery/formation return. No replacement boss waves.

The local four-frame sheet selects poses without changing simulation/RNG. Use actual shape/body/projectile filters for geometry, with rects only as broad-phase metadata.

## Arcade feedback (2026-10-26)

Volleys choose a random clamped target within +/-95px horizontally and +/-28px vertically of the current player, rather than exact/predictive aim. Emit three rays at 0.11rad spacing, increasing to five from level eight. Formation fire interval is max(.55,1.75/(1+.035*(wave-1))/difficulty). Immediate attack/dive states and per-cell bunker interactions remain.
