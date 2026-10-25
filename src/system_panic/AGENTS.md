# Runtime memory

Read [the root wiki](../../AGENTS.md), [loader memory](paks/AGENTS.md) and [Pak contracts](../../paks/AGENTS.md).

## Invariants
- Simulation uses seconds, floating point vectors and a fixed 1/120 second step. Drawing never advances state.
- Run RNG is local (`random.Random(seed)`); presentation RNG cannot change gameplay.
- A run continues until defeat. Level n initially spawns n normal enemies (1, 2, 3, ...), with no finite-mode switch or victory state. Old saved `endless` flags are ignored and disappear on save. Per-enemy scaling and Pak-specific splitting remain separate from the +1 initial-enemy progression. Each new level rebuilds fresh obstacles even in solo/locked play.
- Shuffle selects only enabled Paks. Solo holds all components to its one Pak; coherent selects one Pak for all components; remix selects components independently.
- Catalogs are discovered before preferences/menus and passed into the world, renderer, audio and persistence. The default cached catalog is a convenience for programmatic callers. UI rescan replaces the catalog only in the library, never during a run.
- Each remix channel selects only Paks declaring that component. Solo and coherent modes require complete Paks. Six partial Paks can jointly form a playable mix without a complete Pak. Preferences repair missing providers after removal; UI prevents disabling a required provider. If installed coverage is incomplete, show the library/status view and disable starting.
- Pak API 4 uses concrete ABC subclasses in pilot, enemy, weapon, music, background and obstacles folders. Asset handles resolve relative to each component folder; author-owned handle attribute names are never inspected. Music and scenery are independent channels. Core code must not know the names or behavior labels of launch Paks.
- Preserve health/score/wave and pass shared positions through shuffles; a Pak may constrain its adopted position to its locomotion domain (for example a horizontal bottom lane). Replace only changed component instances; reset their relevant AI/locomotion state, clear projectiles and repair overlaps; Pak callbacks decide protection. Locked obstacle health and pilot/enemy instances survive music/background swaps. Each World owns fresh component instances; catalog definitions are never mutable gameplay objects.
- Component-owned sounds use the effects bus and stop on suspend/replacement/level clear/death/run end. Simulation-only worlds have no audio backend. Music streams through its separate preference. Legacy arena/pilot channel locks migrate with preference schema 2.
- The host calls each Pak projectile update exactly once per active step. Projectile integration, hit policy and lifetime are entirely Pak code; weapon and ability clocks are private state.
- Preference loading validates untrusted JSON, rejects unknown Pak IDs, clamps values, and never permits an empty enabled set. Save atomically to the user-data directory (or explicit `--data-dir`).
- Menus, pause, focus loss and transition screens do not consume active gameplay time.
- Periodic randomization pauses only for a 0.25s visual glitch, then resumes automatically with held input. It never enters ready/clear mode or displays a readiness prompt. A completed level instead shows "LEVEL nn CLEARED" for 1s, then starts the next level directly without a glitch or readiness step. The ready introduction belongs only to the first level of a new run.
- Audio failure must not prevent playing. Assets resolve relative to package/project, never the working directory.

## Rule boundary (API 4)
- Pilot/Enemy are shared body data only. Factories choose stats; Pak subclasses/private state own jump/orbit/AI clocks and fragment identity. Shared identity/position/health survive swaps, local state does not.
- WeaponBase.update receives every active input step. The host never gates firing or reads a cooldown field.
- Enemy death callbacks run once after removal and can register arbitrary child factories/rewards. No family, elite, size or splitting rules exist in core.
- ProjectileBase and EffectBase are scheduled objects. The host does not integrate or expire shots, decide teams, damage contacts or implement ricochet, seeking, return, piercing, explosions or lightning.
- move_body resolves geometry and returns Motion normals without changing velocity, jumps or wrapping. apply_damage is neutral arithmetic/protection; hit methods dispatch to Pak policy.

## Level boundary audit (API 4)
- The host no longer supplies aim/factor, spawn distance/placement, arrival/swap protection, level healing/bonuses or pilot death feedback. Paks own these via spawn_position and optional lifecycle callbacks. Demo controls also belong to each pilot; the host's demo adapter only dispatches ordinary input.
- Level arrival: increment wave, clear shots, build(world), repair pilot overlap, on_level_start for all channels, then spawn exactly wave enemies using the enemy's placement/factory. on_level_complete fires once before the clear message; on_shuffle runs after new components/geometry are ready and receives changed channels.
- Obstacles rebuild once per level and on provider change, never for unrelated presentation swaps. Stock generators use private seeded RNGs; geometry, density and difficulty formulas remain external. safe_position accepts neutral optional away_from/clearance constraints.
- world.hit_cover dispatches to the active ObstaclesBase.take_damage hook. Paks choose raw, armored or impervious geometry; host code contains no named obstacle policy.
- Keep body geometry, shared health/protection arithmetic, scheduling, user input/preferences, state transfer and required run flow in core. UI health thresholds are ratios, not assumptions about 100-point hulls.

## Controllers and menu input
- input_devices.py owns SDL mapped-controller lifetime and raw-input normalization, never gameplay. App combines keyboard/gamepad values into unchanged Controls, so API 4 and Pak behavior stay device-independent.
- Use SDL instance IDs for removals; device indices only for opening. Pygame Controller.id is the opening index: obtain the stable identity with device.as_joystick().get_instance_id(), including after reconnect while other devices remain. Last meaningful pad activity selects it. Duplicate JOY events must not cause duplicate controller actions. Missing/unmapped/failed controller backends leave keyboard/mouse available.
- Movement uses per-axis deadzones (saved/clamped gamepad_deadzone) and quantizes accepted stick directions exactly like the D-pad. No analog travel/speed/steering; both inputs share the same normalized digital diagonal and menu repeat values. Menu focus is spatial with directional wrap, .55/.35 stick hysteresis and bounded repeat. Select/back/pause/page buttons act on edges. All visible widgets must be directionally reachable.
- Route, focus and active-device changes require neutral controller input. This prevents held confirm/fire, stuck navigation and reconnect activation. Do not rearm on a Pak shuffle/level change: held gameplay must resume automatically after the established transition.
- Active controller loss pauses/suspends a run, even when another pad remains. Reconnection does not resume. Window focus loss suppresses controller actions until focus returns and controls are released. Devices close on Quit and bounded run completion.
- App.page_history handles nested input/help/preferences pages and returns to pause. Hints follow the last input device; Preferences → Gamepad / Input shows bindings, controller selection and immediate deadzone adjustment.

## Additive API 4 pilot queries
- PilotBase.aim_direction(world) defaults to None; each weapon decides direction/assistance. Shipped weapons prioritize a supplied vector; homing shots preserve explicit intent. Orbit's radial toggle lives only in its pilot, never in host fields/branches.
- PilotBase.status(world) defaults to an empty string; the shell appends live pilot state to either input-device footer. Querying aim/status cannot advance gameplay/RNG.
- The catalog now has twelve complete Paks. Host discovery, menus and scheduling remain generic. New mechanics and difficulty/layout rules live entirely in their role folders. Keep QA and gallery counts derived from the discovered providers.


## Collectibles and owned geometry
- remove_dead increments the shared kill count once per removed enemy. At multiples of ten it calls the active weapon's create_powerup with a copy of the death position, before on_death can move/remove data or add children. All twelve shipped weapons return a local PowerupBase subclass; the additive API 4 default remains None for older external weapons.
- Powerups are scheduled once per active step and own motion, lifetime, collection conditions and rendering. collect_powerup guards membership/alive identity, increments powerups_collected once, then calls the active weapon's on_powerup. Drops retain their original class/assets across swaps; the global count upgrades whichever weapon is active and survives level changes. New runs start at zero. Intermissions/glitches freeze pickups.
- world.cover is obstacle-provider geometry. world.geometry combines it with component-owned shapes registered by set_geometry. Component replacement and World.close clear registrations; weapon code also cleans its own lists. Cover methods own circle/segment overlap, body/projectile filters, contact response, damage and drawing. No named terrain/weapon branches enter the host.
- move_body uses bounded substeps and binary-search shape contacts, skips zero displacement axes and returns normals without prescribing velocity. Shape callbacks may supply their own response. safe_position accepts an optional body for filtering. Attack code queries world.geometry and blocks_projectile; rays use segment_blocked. Never treat a custom shape's bounding rectangle as its actual solid area.
- ObstaclesBase.update schedules dynamic hazards after body/projectile motion. draw_floor is read-only terrain presentation. PowerupBase and all geometry/weapon/obstacle helpers remain external Pak code. The renderer no longer draws a white position dot beneath pilots; Sky Forge chooses a 22px collision radius to match its 44px sprite.

A shape that fully handles its collision response may return True from on_contact; the resolver then suppresses that contact normal in Motion. This prevents caller AI from applying a second reflection. Default contacts return no handled result and preserve neutral normal reporting.


## Display output and volume preferences
- render_resolution is a validated preset string; auto preserves legacy behavior (1280x800 window, desktop fullscreen). Preferences → Display applies output-size/mode changes immediately and saves them. Unsupported modes fall back to automatic windowed output with feedback. F11 retains the chosen output preset while toggling mode.
- Never resize the 1280x800 logical UI canvas, 960x480 arena surface, World coordinates or fixed timestep when changing output. Only the display surface changes. presentation_rect is the single integer letterbox transform used by both blitting and pointer inversion; preserve black-bar rejection and scaled mouse/controller navigation.
- Music/effects controls use VOLUME_STEP=.05 and clamp to 0–1, preserving existing saved values. These changes live only in shell/preferences, never in Paks. The display page participates in nested back history, controller spatial focus and the --screen QA option.
