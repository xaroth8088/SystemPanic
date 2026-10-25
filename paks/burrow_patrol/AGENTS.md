# Burrow Patrol

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak inspired by Dig Dug, using original art/music/effects rather than copied game assets.

Drill through the rock veins and inflate burrowing worms with a pressure tether.

Each role folder is independently copyable as a partial Pak. Level number controls local difficulty; procedural obstacles use a separate seeded RNG. Keyboard/gamepad share Controls. Preserve +1 initial enemy progression and the core's existing transitions.

Current package behavior: Dig rock and pump nearby enemies within tether reach. Burrowing cells improve range and pressure. The weapon folder owns powerup.py and its upgrade formulas; the engine owns the tenth-kill cadence and shared pickup count.
