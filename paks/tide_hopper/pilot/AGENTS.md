# Tide Hopper: pilot

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Hops have a landing target and travel timer rather than teleporting. Held directions repeat after a gate; a special press makes a longer protected ferry hop. Clear landing state on a level start.

Facing refinement: the local pilot sheet is 4 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/S/W/N. Original built-in imagegen source: assets/images/tide_hopper-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection. Pilot QA emits only eight digital directions and ordinary held/released buttons; live movement keeps the same Controls contract.

Playtest refinement: local grid.py owns 48px cells centered at 24+48k; level arrivals select a clear center. Ordinary hops travel 48px, ferry hops 96px. Targets and the traversed passage must pass actual body/shape queries; a blocked hop stops without snapping through geometry.

## Arcade feedback (2026-10-26)

Ordinary and long ferry hops no longer grant movement invulnerability. Arrival/shuffle safety and the existing post-hit cooldown remain local. Its read-only draw override omits the protection circle while preserving hit blinking. No circle is emitted on a hop; grid positions and travel policy are unchanged.
