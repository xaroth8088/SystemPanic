# Neon Breach: pilot

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Perimeter distance drives the four-edge paddle using left/right only. Vertical input is ignored, including held/edge changes; the special still adds a corner burst. Movement/body orientation stay local.

Facing refinement: the local pilot sheet is 4 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/S/W/N. Original built-in imagegen source: assets/images/neon_breach-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection. The four poses face inward from the current perimeter side. Pilot QA emits only eight digital directions and ordinary held/released buttons; live movement keeps the same Controls contract.

## Arcade feedback (2026-10-26)

The existing four-facing art is fitted to an 84x24 paddle, rotated vertically on side edges. Centers travel 12px from each edge so visible art and rectangular footprint sit flush on all four sides, including initial/level presentation. Paddle, a local Pilot subclass, overrides the neutral overlaps_circle query for its rectangle. Body radius remains the nominal terrain/query radius. The optional read-only PilotBase.draw hook owns alignment. Firing assistance retains the weapon's prior policy; there is no new explicit pilot aim restriction.
