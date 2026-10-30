# Neon Breach

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak with endless +1 initial enemy progression and six independently copyable role folders. No other Pak imports or host feature traits.

Intercept plasma on the perimeter: good paddle returns build power; missed returns drain it.

Weapon: Pool 2+min(3,floor(n/2)); no continuous homing. Energy starts 1.2, loses .35 per missed border and expires below .25. Paddle contact adds .65 up to 2.4, speed +65 capped 760, and adjusts angle with impact offset/tangential paddle velocity. Damage (20+6n)*energy; finite lifetime/hit clocks.

Opposition: Brick drones drift and mark a predicted target for .55s before firing. The aim marker is visual only; scaled shots and movement remain enemy-local.

Four-frame pilot/enemy/weapon/terrain rows and an animated collectible use the original source `assets/images/neon_breach-renewal-source.png`. The local scenery, music and effects are installed; exact prompts, source hashes, measured extraction and mastering operations are in the asset ledgers. Generation is development-only.

Read [renewal verification](../../docs/pak-renewal.json) for the current tested checkpoint and limits. QA uses ordinary digital Controls, with no health, resource or damage grants.

Facing refinement: the local pilot sheet is 4 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/S/W/N. Original built-in imagegen source: assets/images/neon_breach-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection. The four poses face inward from the current perimeter side.

Wall-facing jets correction (2026-10-29): source columns all have downward jets. The pilot's draw hook now rotates the fitted art toward the attached wall on all four edges, superseding the historical no-rotation/inward-facing presentation description above. See [pilot memory](pilot/AGENTS.md#wall-facing-jets-2026-10-29) for the exact orientation policy and verification link.
