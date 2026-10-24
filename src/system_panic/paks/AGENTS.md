# Pak loader memory

This directory contains the loader and frozen API contract, not game content. Read [external Pak authoring](../../../paks/AGENTS.md) and [the format guide](../../../docs/paks.md). Launch Pak code and assets live outside the Python package under project-root `paks/`.

`discover(roots)` returns a catalog with deterministic ordering, complete/partial component pools and loader issues. Manifest API 1 validates IDs, text, paths, assets, callbacks and inheritance. First valid manifest claims an ID; duplicate manifests are reported. Missing/cyclic inheritance and import failures isolate the affected Pak instead of aborting the library. This is trusted local Python, not a sandbox or remote execution service.

Entry modules and relative helpers use isolated package namespaces. Rescans read fresh source, including helpers with unchanged timestamps. Catalogs are immutable snapshots so an active world keeps its selected definitions. Avoid static content imports, global mutable registries and hardcoded launch IDs.

## Six complete games
| Pak | Pilot | Weapon | Enemies | Arena |
|---|---|---|---|---|
| Signal Runner | direct eight-way strafe | rapid pulse | chasing swarm | signal-room cover |
| Void Drifter | rotate + inertial thrust | piercing lance | splitting asteroids | open starfield |
| Iron Circuit | constant drive + steering | bouncing scatter | stationary gun turrets | circuit islands |
| Sky Forge | gravity + double jump | explosive arc | hopping crawlers | platforms |
| Phase Garden | discrete dash steps + blink | chaining lightning | teleporting phantoms | garden maze |
| Orbit Keeper | angular/radial orbit | returning glaives | orbiting sentinels | concentric ruins |

## Compatibility rules
Use engine-owned positions, velocity, health and IDs. Never copy opaque state from one behavior to another. All weapons support aim assistance so different locomotion styles can clear every enemy family; controller-specific secondary actions remain distinct. Cover can be destroyed by every weapon. Every combination needs bounded simulation coverage and safe spawn/relocation.
