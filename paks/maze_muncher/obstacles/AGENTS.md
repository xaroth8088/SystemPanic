# Maze Muncher: obstacles

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Disconnected maze elbows retain wide corridors; never seal a room or assume the pilot grid controls collision geometry. take_damage returns zero: walls are impervious, including to mixed shots, drilling and enemy attacks. Layouts still regenerate every level.

Renewal: local four-frame horizontal terrain animation. Presentation stays inside the actual collision footprint; sprite selection/drawing cannot mutate simulation.

Playtest refinement: obstacles build a fresh seeded 30×15 maze of 32px tiles, with DFS passages, braided alternate routes, a central room and an open row-seven east/west tunnel. Both local actors and the weapon’s lunge/knockbacks wrap x; vertical borders remain solid. Grid centers are 16+32k. Independently copied pilot/enemy navigation uses actual shape filters and horizontal wrap links. Off-grid knockbacks recover by completing the small alignment leg before following a corridor; finite-step corner correction remains collision-checked. This prevents nearest-cell reversal stalls without changing the Controls contract.

## Arcade feedback (2026-10-26)

The full center-row clearing is removed. One seeded odd exit row is selected each build; short stubs at columns 0 and 28/29 connect the ordinary carved maze at columns 1/27. Interior walls still interrupt the row, so wrapping requires navigating maze routes. Paired east/west openings vary in height with seed/level. The existing geometry-filtered wrap graph and local motion need no tunnel-row registry or cross-role lookup. Draw only exit arrows, without a continuous center dotted line.
