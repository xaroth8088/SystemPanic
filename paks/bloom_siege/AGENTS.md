# Bloom Siege

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak, independently installed and playable without any other Pak.

The weapon owns two nonblocking nectar wells, a watering can and plants. Stand still at a well with Fire released to refill at two nectar/second. Hold Fire to sow spaced seeds and water the nearest growing plant within 95px; a mature plant consumes one nectar over about 1.18s. Time alone never grows seeds. Release triggers blooms; growth below 0.2 is harmless. The can starts empty with capacity four, gains two capacity per pickup (maximum 24), and retains water across levels. Nectar wells supply no healing.

Every role is independently copyable as a partial Pak; imports stay in that role or the public engine API. Rules, difficulty, protection/recovery, score rewards, projectiles and geometry remain local. The engine still supplies endless +1 initial enemy progression, scheduling, body arithmetic and transitions. The later resource refinement uses neutral optional enemy-destruction notifications and weapon QA-control refinement; resource and combat rules remain in the Pak.

The two pool locations vary in both axes each level through seeded cycling regions. Players must move fully outside a pool before creating a plant; the can readout explains this. Existing plants can still be watered from nearby. These layout/sowing policies live in the weapon so partial installations retain them.

Four-frame local spritesheets come from the Pak's own original built-in imagegen atlas. Music and two effects were generated offline with local Stable Audio 3; prompts, seeds, measured extraction rectangles and hashes are in the asset pipeline. Background scenery uses local presentation code. No runtime generation or network.

Original expansion snapshot (before the resource/charge refinement), verified 2026-10-26: independent full install, independently copied partial roles, input/release mechanics, rendering purity, seed/level terrain, upgrades and source/frozen controller/collectible checks. All three relaxed digital-input samples clear twelve levels and continue into level thirteen. Standard difficulty and human balance limits are recorded in the newest [verification memory](../../tests/AGENTS.md); these samples are not an ending or a human playtest.

Facing refinement: the local pilot sheet is 8 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/SE/S/SW/W/NW/N/NE. Original built-in imagegen source: assets/images/bloom_siege-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection.
