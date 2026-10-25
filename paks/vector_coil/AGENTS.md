# Vector Coil

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak inspired by Qix and Tron, using original art/music/effects rather than copied game assets.

Hold Fire to draw a tail following the pilot. Close a loop by crossing that tail to defeat fully enclosed enemies. Release Fire to reset. There are no beams or projectiles. Baseline live lines bounce enemies; collected upgrades charge their contacts. Captured interiors become owned solid regions with walkable borders, released on new levels or weapon removal.

Each role folder is independently copyable as a partial Pak. Level number controls local difficulty; procedural obstacles use a separate seeded RNG. Keyboard/gamepad share Controls. Preserve +1 initial enemy progression and the core's existing transitions.

Current package behavior: Close a tail to capture enemies and carve solid territory. Enemies bounce off live lines; cells charge them. The weapon folder owns powerup.py and its upgrade formulas; the engine owns the tenth-kill cadence and shared pickup count.
