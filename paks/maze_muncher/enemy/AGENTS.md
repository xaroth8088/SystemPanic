# Maze Muncher: enemy

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). Copy this entire role folder as a partial Pak. Actor factories, local helpers, spawn/difficulty/reward policy and contacts belong here. No private sibling-role state or host feature traits.

Crabs alternate direct/predictive/flanking chase and scatter. Hits stun for .2s; stunned contacts are harmless. Local shape-aware route planning prevents persistent wall pushing. The pilot retains its own energized-contact special.

The local four-frame sheet selects poses without changing simulation/RNG. Owned transient cues recreate after world cleanup; death clears them. Use actual shape/body/projectile filters for geometry, with rects only as broad-phase metadata.

Navigation optimization: crabs share read-only nodes/links within their component instance when the effective blocking set has identical rectangular topology and radius. This includes subclasses inheriting Cover.overlaps_circle; effective per-body filters are part of the key. Arbitrary class/instance overlap overrides retain separate graph construction and actual shape queries. Waypoints, BFS visits, timers and bodies remain independent. Cache clears on level/shuffle and retains at most eight recent snapshots.

Playtest refinement: obstacles build a fresh seeded 30×15 maze of 32px tiles, with DFS passages, braided alternate routes, a central room and an open row-seven east/west tunnel. Both local actors and the weapon’s lunge/knockbacks wrap x; vertical borders remain solid. Grid centers are 16+32k. Independently copied pilot/enemy navigation uses actual shape filters and horizontal wrap links. Off-grid knockbacks recover by completing the small alignment leg before following a corridor; finite-step corner correction remains collision-checked. This prevents nearest-cell reversal stalls without changing the Controls contract.

## Moving-mirror navigation performance (2026-10-26)

The saved BUGGY mix exposed per-enemy full-grid rebuilding against Glasswake's moving rectangular mirrors. Navigation now filters the effective blockers once per query, shares valid rectangle snapshots, and bounds their LRU history to eight. A read-only lattice template contains exact original sampled coordinates and point-to-edge incidence. Rectangle rebuilds inspect only probe buckets near expanded bounds, then call the actual inherited overlap method; no collision shape is approximated. Arbitrary custom overlap methods stay on the conservative per-body sampled path, with per-query point memoization. No coordinate rounding, AI cadence change, stopped mirrors or host content rule is introduced. The paired four-second saved-mix probes retain identical body/projectile/RNG state hashes at 1/8/20 enemies. See [performance evidence](../../../docs/buggy-performance.json).

## Quiet presentation and tail routing (2026-10-28)

The Iron/Maze/Vector/Tide mix exposed custom live-tail graphs rebuilding per enemy and per new shape identity. Navigation now shares only explicit immutable navigation_key snapshots, including Vector segments/polygons, and indexes their promised conservative bounds before calling exact overlaps_circle. Recreated equal shapes reuse nodes/links; every effective body filter and radius still applies. Unknown custom queries keep the prior body-local conservative path; history remains bounded to eight. Indexed and conservative graphs match exactly, and paired two-second 1/8/20-enemy runs retain body/tail/score/RNG hashes. See docs/visual-cleanup.json for timings and limits.
