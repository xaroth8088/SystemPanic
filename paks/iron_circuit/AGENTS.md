# Iron Circuit

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak with endless +1 initial enemy progression and six independently copyable role folders. No other Pak imports or host feature traits.

Drive fast to strengthen plasma; bank it into turret firing and recovery windows.

Weapon: Base damage (12+4n)*(.5+2*min(1,actual_speed/430)). Speed is measured from resolved body displacement, so pushing a wall does not power shots. Each bank adds .75 base damage up to 2.25 bonus; bounce budget 4+floor(n/3). Track rails pass shots. Pellet/cadence formulas remain local.

Opposition: Turrets lock a lane for .55s, fire it, and recover for .7s. Damage multipliers idle .5, windup .9, recovery 1.45. Later alternating fans remain; cues own no damage.

Four-frame pilot/enemy/weapon/terrain rows and an animated collectible use the original source `assets/images/iron_circuit-renewal-source.png`. The local scenery, music and effects are installed; exact prompts, source hashes, measured extraction and mastering operations are in the asset ledgers. Generation is development-only.

Read [renewal verification](../../docs/pak-renewal.json) for the current tested checkpoint and limits. QA uses ordinary digital Controls, with no health, resource or damage grants.

Facing refinement: the local pilot sheet is 8 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/SE/S/SW/W/NW/N/NE. Original built-in imagegen source: assets/images/iron_circuit-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection.

## Arcade feedback (2026-10-26)

The pilot now uses the original single-pose crop from assets/images/sprites-source.png, restored byte-for-byte with its original provenance. sprite returns the raw ImageAsset; sprite_angle rotates it by -degrees(body.angle)-90. Movement, abilities, acceleration, gravity and weapon formulas were retained. authoring.component_grids.pilot=[1,1] and pilot_rendering=rotated_single preserve this choice through later asset exports. Earlier facing/renewal descriptions above describe historical asset checkpoints.
