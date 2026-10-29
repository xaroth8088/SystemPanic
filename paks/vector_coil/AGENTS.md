# Vector Coil

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak with endless +1 initial enemy progression and six independently copyable role folders. No other Pak imports or host feature traits.

Draw and close territory loops around whole enemies; release to abandon a tail.

Weapon: A new loop of area >=900 captures fully contained enemy circles. Baseline live tails bounce without damage. Upgrades add 4n contact damage per enemy per .4s, width 2+min(6,.5n) and length 6000+500n. Filled solid territory has a walkable boundary, lasts 22 active seconds, and dims in its last four seconds. This avoids permanent capture dead ends. Level/removal clears owned geometry; unrelated presentation swaps preserve it for its remaining lifetime.

Opposition: Sparks retain level-scaled movement, periodic pursuit turns and real shape/border reflections. Capture and trail damage remain the weapon role, never a pilot passive or host rule.

Four-frame pilot/enemy/weapon/terrain rows and an animated collectible use the original source `assets/images/vector_coil-renewal-source.png`. The local scenery, music and effects are installed; exact prompts, source hashes, measured extraction and mastering operations are in the asset ledgers. Generation is development-only.

Read [renewal verification](../../docs/pak-renewal.json) for the current tested checkpoint and limits. QA uses ordinary digital Controls, with no health, resource or damage grants.

Playtest refinement: a live path anchored on an existing capture can close against its connected boundary network. network.py splits old edges at anchors/intersections and finds a connected boundary path; new open edges plus that path define the capture polygon. Disconnected old regions do not connect, walking only old outlines does not recapture, and expired regions leave the network. Whole-circle containment, 900px² minimum and 22s region lifetime still apply.

Facing refinement: the local pilot sheet is 4 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/S/W/N. Original built-in imagegen source: assets/images/vector_coil-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection.
