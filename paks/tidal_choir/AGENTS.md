# Tidal Choir

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak, independently installed and playable without any other Pak.

Only bubbles with release radius at least 30px (0.6s charge) can entrain enemies or deal burst damage. Smaller bubbles drift and pop harmlessly, even after upgrades. The weapon readout marks the minimum charge. Pickups improve powered burst size/damage without bypassing this threshold.

Attack bubbles rebound at all screen borders with 65% retained velocity instead of bursting on contact. Their existing fuse continues after the rebound; powered bubbles still burst after 1.35s and undersized bubbles remain harmless.

Every role is independently copyable as a partial Pak; imports stay in that role or the public engine API. Rules, difficulty, protection/recovery, score rewards, projectiles and geometry remain local. The engine still supplies endless +1 initial enemy progression, scheduling, body arithmetic and transitions. The later resource refinement uses neutral optional enemy-destruction notifications and weapon QA-control refinement; resource and combat rules remain in the Pak.

Four-frame local spritesheets come from the Pak's own original built-in imagegen atlas. Music and two effects were generated offline with local Stable Audio 3; prompts, seeds, measured extraction rectangles and hashes are in the asset pipeline. Background scenery uses local presentation code. No runtime generation or network.

Original expansion snapshot (before the resource/charge refinement), verified 2026-10-26: independent full install, independently copied partial roles, input/release mechanics, rendering purity, seed/level terrain, upgrades and source/frozen controller/collectible checks. All three relaxed digital-input samples clear twelve levels and continue into level thirteen. Standard difficulty and human balance limits are recorded in the newest [verification memory](../../tests/AGENTS.md); these samples are not an ending or a human playtest.

Facing refinement: the local pilot sheet is 8 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/SE/S/SW/W/NW/N/NE. Original built-in imagegen source: assets/images/tidal_choir-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection.

Enemy presentation (2026-10-28): later jet charges leave a filled violet ink cloud instead of a red circle/X; the charging creature has a short actual-motion wake and matching ink droplets. Hidden delay, damage window, footprint, speed and difficulty stay unchanged. See [enemy memory](enemy/AGENTS.md) for presentation boundaries and fresh verification.
