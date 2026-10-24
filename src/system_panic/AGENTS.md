# Runtime memory

Read [the root wiki](../../AGENTS.md), [loader memory](paks/AGENTS.md) and [Pak contracts](../../paks/AGENTS.md).

## Invariants
- Simulation uses seconds, floating point vectors and a fixed 1/120 second step. Drawing never advances state.
- Run RNG is local (`random.Random(seed)`); presentation RNG cannot change gameplay.
- A run continues until defeat. Level n initially spawns n normal enemies (1, 2, 3, ...), with no finite-mode switch or victory state. Old saved `endless` flags are ignored and disappear on save. Per-enemy scaling and Pak-specific splitting remain separate from the +1 initial-enemy progression.
- Shuffle selects only enabled Paks. Solo holds all components to its one Pak; coherent selects one Pak for all components; remix selects components independently.
- Catalogs are discovered before preferences/menus and passed into the world, renderer, audio and persistence. The default cached catalog is a convenience for programmatic callers. UI rescan replaces the catalog only in the library, never during a run.
- Each remix channel selects only Paks declaring that component. Solo and coherent modes require complete Paks. Six partial Paks can jointly form a playable mix without a complete Pak. Preferences repair missing providers after removal; UI prevents disabling a required provider. If installed coverage is incomplete, show the library/status view and disable starting.
- Pak API 3 uses concrete ABC subclasses in pilot, enemy, weapon, music, background and obstacles folders. Asset handles resolve relative to each component folder; author-owned handle attribute names are never inspected. Music and scenery are independent channels. Core code must not know the names or behavior labels of launch Paks.
- Preserve health/score/wave and positions during shuffles. Replace only changed component instances; reset their relevant AI/locomotion state, clear projectiles, grant invulnerability and repair overlaps. Locked obstacle health and pilot/enemy instances survive music/background swaps. Each World owns fresh component instances; catalog definitions are never mutable gameplay objects.
- Component-owned sounds use the effects bus and stop on suspend/replacement/level clear/death/run end. Simulation-only worlds have no audio backend. Music streams through its separate preference. Legacy arena/pilot channel locks migrate with preference schema 2.
- The host calls each Pak projectile update exactly once per active step. Projectile integration, hit policy and lifetime are entirely Pak code; weapon and ability clocks are private state.
- Preference loading validates untrusted JSON, rejects unknown Pak IDs, clamps values, and never permits an empty enabled set. Save atomically to the user-data directory (or explicit `--data-dir`).
- Menus, pause, focus loss and transition screens do not consume active gameplay time.
- Periodic randomization pauses only for a 0.25s visual glitch, then resumes automatically with held input. It never enters ready/clear mode or displays a readiness prompt. A completed level instead shows "LEVEL nn CLEARED" for 1s, then starts the next level directly without a glitch or readiness step. The ready introduction belongs only to the first level of a new run.
- Audio failure must not prevent playing. Assets resolve relative to package/project, never the working directory.

## Rule boundary (API 3)
- Pilot/Enemy are shared body data only. Factories choose stats; Pak subclasses/private state own jump/orbit/AI clocks and fragment identity. Shared identity/position/health survive swaps, local state does not.
- WeaponBase.update receives every active input step. The host never gates firing or reads a cooldown field.
- Enemy death callbacks run once after removal and can register arbitrary child factories/rewards. No family, elite, size or splitting rules exist in core.
- ProjectileBase and EffectBase are scheduled objects. The host does not integrate or expire shots, decide teams, damage contacts or implement ricochet, seeking, return, piercing, explosions or lightning.
- move_body resolves geometry and returns Motion normals without changing velocity, jumps or wrapping. apply_damage is neutral arithmetic/protection; hit methods dispatch to Pak policy.
