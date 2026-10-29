# Void Drifter

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak with endless +1 initial enemy progression and six independently copyable role folders. No other Pak imports or host feature traits.

Charge a piercing lance, release it, and manage recoil among drifting fragments and gravity hazards.

Weapon: Hold .18-1.15s then release; .22s recovery. With normalized strength s, damage 18+58s+7n, speed 580+330s+min(160,12n), penetration 1+round(3s)+floor(n/2). Recoil 25+90s acts on the public pilot velocity. Short taps produce no lance.

Opposition: Asteroid fracture families, local spawn/reward policy, drift, gravity and comet interactions remain independently owned. New local frames animate the rock states; no family trait is interpreted by the host.

Four-frame pilot/enemy/weapon/terrain rows and an animated collectible use the original source `assets/images/void_drifter-renewal-source.png`. The local scenery, music and effects are installed; exact prompts, source hashes, measured extraction and mastering operations are in the asset ledgers. Generation is development-only.

Read [renewal verification](../../docs/pak-renewal.json) for the current tested checkpoint and limits. QA uses ordinary digital Controls, with no health, resource or damage grants.

Facing refinement: the local pilot sheet is 8 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/SE/S/SW/W/NW/N/NE. Original built-in imagegen source: assets/images/void_drifter-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection.

## Arcade feedback (2026-10-26)

The pilot now uses the original single-pose crop from assets/images/sprites-source.png, restored byte-for-byte with its original provenance. sprite returns the raw ImageAsset; sprite_angle rotates it by -degrees(body.angle)-90. Movement, abilities, acceleration, gravity and weapon formulas were retained. authoring.component_grids.pilot=[1,1] and pilot_rendering=rotated_single preserve this choice through later asset exports. Earlier facing/renewal descriptions above describe historical asset checkpoints.
