# Burrow Patrol

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak with endless +1 initial enemy progression and six independently copyable role folders. No other Pak imports or host feature traits.

Stay within pumping range, maintain pressure, and avoid a worm after its marked emergence.

Weapon: Finite reach min(300,145+18n), pressure .85+.08n/s, gradual damage 7+2n/s, pop max(45,1.25*max_health). A pop has .32s pump recovery. Releasing/missing drains pressure; changing target resets it. PressureLine is visual only and recreates after cleanup.

Opposition: Worms hunt, burrow through terrain for .9s with .65 damage armor, safely emerge for .55s, then rush a locked target for .55s. Burrow/emerge contacts are harmless. Safe-position emergence and all cue/phase rules stay here.

Four-frame pilot/enemy/weapon/terrain rows and an animated collectible use the original source `assets/images/burrow_patrol-renewal-source.png`. The local scenery, music and effects are installed; exact prompts, source hashes, measured extraction and mastering operations are in the asset ledgers. Generation is development-only.

Read [renewal verification](../../docs/pak-renewal.json) for the current tested checkpoint and limits. QA uses ordinary digital Controls, with no health, resource or damage grants.

Facing refinement: the local pilot sheet is 4 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/S/W/N. Original built-in imagegen source: assets/images/burrow_patrol-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection.
