# Runtime memory

Read [the root wiki](../../AGENTS.md) and [Pak contracts](paks/AGENTS.md).

## Invariants
- Simulation uses seconds, floating point vectors and a fixed 1/120 second step. Drawing never advances state.
- Run RNG is local (`random.Random(seed)`); presentation RNG cannot change gameplay.
- Shuffle selects only enabled Paks. Solo holds all components to its one Pak; coherent selects one Pak for all components; remix selects components independently.
- Preserve health/score/wave and positions during shuffles; reset AI and locomotion state, clear hostile projectiles, grant invulnerability and repair overlaps.
- Each projectile is advanced exactly once per simulation step. Cooldowns use simulation time.
- Preference loading validates untrusted JSON, rejects unknown Pak IDs, clamps values, and never permits an empty enabled set. Save atomically to the user-data directory (or explicit `--data-dir`).
- Menus, pause, focus loss and transition screens do not consume active gameplay time.
- Periodic randomization pauses only for a 0.25s visual glitch, then resumes automatically with held input. It never enters ready/clear mode or displays a readiness prompt. A completed level instead shows "LEVEL nn CLEARED" for 1s, then starts the next level directly without a glitch or readiness step. The ready introduction belongs only to the first level of a new run.
- Audio failure must not prevent playing. Assets resolve relative to package/project, never the working directory.
