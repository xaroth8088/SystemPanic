# Maze Muncher

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak with endless +1 initial enemy progression and six independently copyable role folders. No other Pak imports or host feature traits.

Buffer cardinal turns, lunge into a target, and chase stronger backbites through the maze.

Weapon: Forward swept lunge 460 px/s for .14+min(.08,.008n), damage 20+5n, cooldown max(.3,.62/(1+.035n)). Hitting a foe moving away in the lunge direction deals x1.75. One hit ends the dash, separates both bodies through move_body, and grants .22s safe separation. No attack projectile is launched.

Opposition: Crabs alternate direct/predictive/flanking chase and scatter. Hits stun for .2s; stunned contacts are harmless. Local shape-aware route planning prevents persistent wall pushing. The pilot retains its own energized-contact special.

Four-frame pilot/enemy/weapon/terrain rows and an animated collectible use the original source `assets/images/maze_muncher-renewal-source.png`. The local scenery, music and effects are installed; exact prompts, source hashes, measured extraction and mastering operations are in the asset ledgers. Generation is development-only.

Read [renewal verification](../../docs/pak-renewal.json) for the current tested checkpoint and limits. QA uses ordinary digital Controls, with no health, resource or damage grants.

Playtest refinement: obstacles build a fresh seeded 30×15 maze of 32px tiles, with DFS passages, braided alternate routes, a central room and an open row-seven east/west tunnel. Both local actors and the weapon’s lunge/knockbacks wrap x; vertical borders remain solid. Grid centers are 16+32k. Independently copied pilot/enemy navigation uses actual shape filters and horizontal wrap links. Off-grid knockbacks recover by completing the small alignment leg before following a corridor; finite-step corner correction remains collision-checked. This prevents nearest-cell reversal stalls without changing the Controls contract.

Facing refinement: the local pilot sheet is 4 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/S/W/N. Original built-in imagegen source: assets/images/maze_muncher-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection.

## Arcade feedback (2026-10-26)

The full center-row clearing is removed. One seeded odd exit row is selected each build; short stubs at columns 0 and 28/29 connect the ordinary carved maze at columns 1/27. Interior walls still interrupt the row, so wrapping requires navigating maze routes. Paired east/west openings vary in height with seed/level. The existing geometry-filtered wrap graph and local motion need no tunnel-row registry or cross-role lookup. Draw only exit arrows, without a continuous center dotted line.

## Moving-mirror navigation performance (2026-10-26)

Enemy route planning now handles moving rectangular obstacle subclasses without rebuilding a complete grid separately for every enemy. Exact probe indexing, per-body filter-safe snapshot sharing and an eight-snapshot cache remain inside the enemy folder. Pilot navigation/live controls are unchanged. See [enemy memory](enemy/AGENTS.md) and [the BUGGY regression](../../docs/buggy-performance.json).
