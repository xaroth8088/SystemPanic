# Sky Forge

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak with endless +1 initial enemy progression and six independently copyable role folders. No other Pak imports or host feature traits.

Stab nearby crawlers or charge a powerful sword throw, then recover the blade while double-jumping between decks.

Weapon: Tap/release below .55s to stab (25+6n damage, 72+min(36,4n) reach, .13s active). Hold .55–1.3s and release to throw the single sword: strength s gives 90+50s+18n damage, speed 620+220s, and gravity 160. The first enemy, solid surface, border or 1.6s flight limit drops the blade; resting gravity is 550. No automatic return or expiry: physically collect it before attacking again. A locked weapon reinserts its unclaimed blade after host projectile cleanup and relocates it safely on terrain/level changes; replacement discards it. Recovery is .28s. Drawing and charge hints are read-only.

Opposition: Crawlers have gravity and flat-foot landings, .38s leap windup, locked jump velocity, and .48s harmless recovery. Lower targets cause committed walks off deck edges. A high pilot triggers a marked .85s/.3s rooftop heat zone that hits once. Local physics/cues/hazards are copied with this enemy folder.

Four-frame pilot/enemy/weapon/terrain rows and an animated collectible use the original source `assets/images/sky_forge-renewal-source.png`. The local scenery, music and effects are installed; exact prompts, source hashes, measured extraction and mastering operations are in the asset ledgers. Generation is development-only.

Read [renewal verification](../../docs/pak-renewal.json) for the current tested checkpoint and limits. QA uses ordinary digital Controls, with no health, resource or damage grants.

Facing refinement: the local pilot sheet is 2 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Sky has right/left running poses plus a jump pose, with the feet aligned to the 44px frame bottom. Original built-in imagegen source: assets/images/sky_forge-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection.

## Arcade feedback (2026-10-26)

Short attacks are overhead sweeps with a small collision-respecting knockback; charged throws still require physical recovery. Both actors now meet the true floor and crawler poses align their feet locally. See the pilot, enemy and weapon memories for current mechanics; older stab descriptions are historical.
