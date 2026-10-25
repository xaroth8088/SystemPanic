# Maze Muncher

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak inspired by Pac-Man, using original art/music/effects rather than copied game assets.

Buffer cardinal turns through impervious maze walls. Normal fire is a forward contact dash: one hit knocks both pilot and target apart. The energized contact special remains separate.

Each role folder is independently copyable as a partial Pak. Level number controls local difficulty; procedural obstacles use a separate seeded RNG. Keyboard/gamepad share Controls. Preserve +1 initial enemy progression and the core's existing transitions.

Current package behavior: Lunge forward to strike and bounce apart. Fixed power pellets strengthen the dash. The weapon folder owns powerup.py and its upgrade formulas; the engine owns the tenth-kill cadence and shared pickup count.
