# Neon Breach

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak inspired by Breakout, using original art/music/effects rather than copied game assets.

Circle the perimeter and bank an accelerating plasma ball through brick drones.

Each role folder is independently copyable as a partial Pak. Level number controls local difficulty; procedural obstacles use a separate seeded RNG. Keyboard/gamepad share Controls. Preserve +1 initial enemy progression and the core's existing transitions.

Current package behavior: Slide the perimeter with left/right; vertical input is unused. Bouncing bonus balls strengthen multiball. The weapon folder owns powerup.py and its upgrade formulas; the engine owns the tenth-kill cadence and shared pickup count.
