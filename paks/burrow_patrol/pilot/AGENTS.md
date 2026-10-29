# Burrow Patrol: pilot

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Cardinal movement erodes rock ahead. The special excavates nearby cover and damages nearby enemies while giving a temporary movement boost. Demo input kites/predicts threats rather than ramming targets.

Digging/excavation dispatches through world.hit_cover, so an impervious obstacle provider remains impervious.

Facing refinement: the local pilot sheet is 4 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/S/W/N. Original built-in imagegen source: assets/images/burrow_patrol-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection. Pilot QA emits only eight digital directions and ordinary held/released buttons; live movement keeps the same Controls contract.
