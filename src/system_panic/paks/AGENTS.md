# Pak memory and authoring

Each Pak supplies a frozen `Pak` definition with its own pilot, weapon, enemy family, arena, colors, instructions and asset identifiers. Each module owns its `move`, `fire`, `advance_enemy` and `make_arena` callbacks; the core dispatches these instead of branching on behavior names. Registry validation rejects duplicate IDs and missing callbacks. Add a file here and register its exported definition in `registry.py`. See [the interface guide](../../../docs/architecture.md).

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
