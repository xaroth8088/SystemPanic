# Vector Coil: pilot

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Continuous cardinal movement and shielded reversing belong to this pilot. It neither draws damaging trails nor deals passive trail damage; the capture tail is entirely the weapon component. Demo controls trace a perimeter with ordinary inputs.

Facing refinement: the local pilot sheet is 4 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/S/W/N. Original built-in imagegen source: assets/images/vector_coil-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection. Pilot QA emits only eight digital directions and ordinary held/released buttons; live movement keeps the same Controls contract.

QA navigates to an outer corner without drawing, then traces complete cardinal edges with normal Fire input. Entry waypoints are committed until reached, and the route resets on each level. Neither this pilot nor its QA directly captures, damages or grants health.
