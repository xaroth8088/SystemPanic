# Orbit Keeper

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak with endless +1 initial enemy progression and six independently copyable role folders. No other Pak imports or host feature traits.

Choose inward/outward radial attacks and time returning blade catches.

Weapon: Pool 2+min(3,floor(n/3)). Damage 28+5n; outgoing speed 600+min(160,20n), outgoing time .55+min(.25,.025n). One hit per enemy on each leg; return damage x1.15 and returning blades pass cover. Release after holding >=.35s to arm a .22s catch window. A caught blade empowers the next launch x1.8 (nonstacking) and grants .15s protection.

Opposition: Sentinels orbit, lock a lane for .5s and expose for .85s after shooting. Damage multipliers guard .55, aim .8, open 1.4. Formation shift, difficulty, shots and rewards stay local.

Four-frame pilot/enemy/weapon/terrain rows and an animated collectible use the original source `assets/images/orbit_keeper-renewal-source.png`. The local scenery, music and effects are installed; exact prompts, source hashes, measured extraction and mastering operations are in the asset ledgers. Generation is development-only.

Read [renewal verification](../../docs/pak-renewal.json) for the current tested checkpoint and limits. QA uses ordinary digital Controls, with no health, resource or damage grants.

## Arcade feedback (2026-10-26)

The pilot now uses the original single-pose crop from assets/images/sprites-source.png, restored byte-for-byte with its original provenance. sprite returns the raw ImageAsset; sprite_angle rotates it by -degrees(body.angle)-90. Movement, abilities, acceleration, gravity and weapon formulas were retained. authoring.component_grids.pilot=[1,1] and pilot_rendering=rotated_single preserve this choice through later asset exports. Earlier facing/renewal descriptions above describe historical asset checkpoints.
