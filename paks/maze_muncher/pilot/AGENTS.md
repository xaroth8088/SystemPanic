# Maze Muncher: pilot

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Buffer cardinal turns near 32-pixel grid lines. A blocked move permits an unsnapped escape turn because mixed cover need not align to the grid. Energized contact damage belongs to the pilot.

Facing refinement: the local pilot sheet is 4 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/S/W/N. Original built-in imagegen source: assets/images/maze_muncher-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection. Pilot QA emits only eight digital directions and ordinary held/released buttons; live movement keeps the same Controls contract.

Grid snaps are rejected if the proposed center overlaps actual body-blocking geometry. QA commits to reachable grid waypoints; it must not retain a moving target's off-grid point because buffered turns cannot reach that coordinate. Enemy routing is separately owned in the enemy folder.

Playtest refinement: obstacles build a fresh seeded 30×15 maze of 32px tiles, with DFS passages, braided alternate routes, a central room and an open row-seven east/west tunnel. Both local actors and the weapon’s lunge/knockbacks wrap x; vertical borders remain solid. Grid centers are 16+32k. Independently copied pilot/enemy navigation uses actual shape filters and horizontal wrap links. Off-grid knockbacks recover by completing the small alignment leg before following a corridor; finite-step corner correction remains collision-checked. This prevents nearest-cell reversal stalls without changing the Controls contract.

## Quiet presentation and tail routing (2026-10-28)

The original 1262x1246 facing source has uneven animation bands. Measured row edges [0,316,603,895,1246] replace uniform-quarter source cuts in export_facings.py. All sixteen complete subject crops are centered losslessly into equal output frames; E/S/W/N selection is unchanged. Source pixels/provenance are retained, with updated derivative geometry/hash records. This fixes the truncated final south-facing pose and neighboring-row bleed without generating new art.
