# Installing and authoring Paks

Paks are local folders discovered at startup and by **Rescan Paks** in the library. The six launch games use this same loader. Each folder contains `pak.json`, its assets, and (when supplying new behavior) Python code. No core registry edit or executable rebuild is required.

Default locations are `paks/` beside `SystemPanic.exe` in the Windows distribution, project-root `paks/` in a checkout, or `share/system-panic/paks` in a Python installation. A second location is the user's data folder: `%LOCALAPPDATA%/SystemPanic/paks` on Windows, or `$XDG_DATA_HOME/SystemPanic/paks` (default `~/.local/share/SystemPanic/paks`) elsewhere. Use **Pak status** to see locations and skipped-Pak errors. The library paginates automatically.

`python play.py --pak-dir path/to/paks` replaces default locations for that launch; repeat the option for multiple roots. `--list-paks` prints discovered IDs, components, solo eligibility and errors. `--solo ID` accepts complete Paks only. The same switches work on the Windows executable. Add or remove Pak folders while in the library, then rescan. Existing runs keep their catalog snapshot.

## Complete and partial Paks

`components` lists the channels a Pak supplies: `pilot`, `weapon`, `enemy`, `arena`. All four make a complete Pak, eligible for solo play and coherent shuffle. Any smaller nonempty set makes a partial Pak, labeled **MIX ONLY** in the library. Partial Paks join only their declared pools during component remix. Enabled Paks collectively must cover all four channels; four complementary partial Paks can run without any complete Pak. Coherent shuffle uses complete Paks, so a partial-only installation uses component remix.

Here is a weapon-only Pak with its own behavior and sprite:

```json
{
  "api_version": 1,
  "id": "plasma_arc",
  "version": "1.0.0",
  "name": "Plasma Arc",
  "subtitle": "WEAPON / PIERCING",
  "description": "A piercing plasma weapon for the remix pool.",
  "color": [80, 220, 255],
  "components": ["weapon"],
  "weapon": "plasma_arc",
  "cooldown": 0.3,
  "entrypoint": "pak.py",
  "assets": {"sprites": {"weapon": "assets/projectile.png"}}
}
```

Its `pak.py` can be this small:

```python
def fire(world, direction):
    world.spawn_shot(direction, "plasma_arc", damage=28, speed=550, pierce=2)
```

Use your own generated local PNG/WebP for the sprite. A Pak providing all four components supplies all four callbacks and sprite entries. Each component also has a behavior label (`pilot`, `weapon`, `enemy` or `arena`) for diagnostics. A new pilot supplies `controls` and `special` text. Optional `assets.music` points to local OGG/WAV music, played when that Pak supplies the pilot. Paths stay inside the Pak folder, including symlink resolution.

## Asset-only variations

A partial Pak can reuse installed behavior and supply different assets without any Python entrypoint:

```json
{
  "api_version": 1,
  "id": "alternate_pulse",
  "version": "1.0.0",
  "name": "Alternate Pulse",
  "subtitle": "WEAPON / VISUAL VARIANT",
  "description": "A new projectile appearance using Signal Runner's pulse behavior.",
  "color": [255, 160, 100],
  "components": ["weapon"],
  "inherits": {"weapon": "signal_runner"},
  "assets": {"sprites": {"weapon": "assets/projectile.png"}}
}
```

Inheritance is per component. Inherited callbacks, cooldowns, enemy splitting, pilot instructions and presentation defaults follow their provider. Local metadata can override supported values. The provider must also be installed (it need not be enabled in the mix). Dependency order is resolved automatically. Missing providers and cycles appear in Pak status.

## Behavior API 1

| Component | Required callback | Optional callbacks |
|---|---|---|
| Pilot | `move(world, dt, control, jump, special)` | `prepare_pilot(world)`, `demo_controls(world)` |
| Weapon | `fire(world, direction)` | — |
| Enemy | `advance_enemy(world, enemy, dt)` | — |
| Arena | `make_arena()` returning fresh `list[Cover]` | `draw_arena(surface)` |

Import shared state/types from `system_panic.model`, for example `Vec`, `Cover`, `Beam`, `Controls`, `WIDTH`, `HEIGHT`, `unit`, `normalized`, `circle_rect`. Relative helper imports such as `from .weapons import fire` stay isolated from other Paks. The loader reads fresh source on rescan, including helpers. Pak code is trusted local Python with normal process permissions; it is not sandboxed. The game does not download Paks or install their dependencies.

The engine owns fixed-step simulation, damage, projectile advancement, health/score/level persistence, endless progression and shuffle transitions. Use `world.move_body` and `safe_position` for collision and placement. Use `spawn_shot`, `enemy_shot`, `damage_enemy`, `burst` and `beams` for combat/effects. The engine advances enemy `age` and `timer` before calling its AI. `prepare_pilot` runs after clean pilot state is created; `draw_arena` must not mutate simulation. `demo_controls` returns ordinary `Controls` for QA and is optional.

Automatic swaps run only when an enabled, unlocked component has an alternative provider (or coherent mode has multiple complete Paks). A mix with one provider per component stays locked and does not interrupt play with redundant glitches.

Optional metadata includes `order` (integer, default 100), `cooldown` (positive seconds), `splits` (enemy fragments, default 0), and `presentation`: `pilot_sprite` is `upright`, `rotate`, or `face`; `rotate_enemy` is boolean. Sprite roles are independent; there is no shared-atlas geometry in the runtime. IDs are unique lowercase identifiers of up to 64 characters. Roots are searched in order; duplicate IDs are reported and the first validated manifest claims the ID. Unsupported API versions, missing local files/callbacks and import failures skip that Pak while other valid Paks still load.

Test complete Paks alone and partial Paks in valid mixes with current components. `python tools/compatibility.py` uses the Cartesian product of eligible providers for each channel. Both it and `tools/verify.py` accept repeated `--pak-dir` options for isolated Pak roots. Restart or rescan after code/asset changes; changing files does not mutate an active run.
