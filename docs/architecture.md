# Runtime and Pak architecture

App owns windows, menus, preferences, input and playback. World owns engine state and 120 Hz fixed-step simulation. Graphics draws without advancing state. tools/assetforge is a separate generation/export pipeline; the game only reads finished local assets.

Gamepads in input_devices.py use SDL's mapped controller API, distinguish connection indices from instance IDs and select the last actively used connected pad. Radial deadzones normalize analog travel; D-pad/buttons/triggers become the same Controls values as keyboard input. Paks stay device-independent. App owns spatial menu focus, select/back/pause/page actions and input hints. A neutral-input gate protects route/focus/device transitions, while menu repeat has separate hysteresis/timing. No gate runs on a Pak shuffle or level change. Active-device loss pauses and suspends the world; reconnection never resumes automatically. Nested page history preserves the return path through controls/preferences/pause.

Level n starts with n normal enemies. Play continues until defeat, with no finite-run toggle or finale. Existing health/speed scaling and Pak-specific fragments remain. Periodic swaps pause for a 0.25s visual glitch and resume held controls. Level clears show their message for one second and enter the next level directly; only a new run has the initial introduction.

## Definitions and instances

Content lives under external paks/<id>/ folders. Each role folder contains its class and assets: pilot, enemy, weapon, music, background and obstacles. The public contract is six ABCs in system_panic.pak_api. See [the complete guide and examples](paks.md).

pak.json declares API 4, display metadata and component selection/configuration. The loader validates and builds immutable ComponentSpec definitions (class, asset directory and optional overrides). Catalogs are passed to preferences, simulation, rendering and audio; there is no static launch-game registry.

World.component(channel) creates a run-owned instance with an asset context and optional audio service, then calls activate(world). init() loads local handles before world activation. Authors choose their own handle/counter attribute names; only explicit ABC methods/properties are API. World provides typed overloads for literal component names.

Instances remain while their selected provider stays unchanged. Replacements call deactivate/suspend, discard private state and instantiate fresh behavior. Worlds never share mutable component state. Preview objects are separate instances with no world/audio service.

## Component responsibilities

PilotBase.create() and EnemyBase.create() own actor stats/local state. Their active callbacks receive raw input or a simulation step; the host does not infer input edges, firing readiness, enemy clocks, contact damage, recovery or rewards. Weapons schedule their own attacks. Enemy death hooks decide transformations and child spawns. The removed family/splits/cooldown traits have no replacement feature flags in the host.

Body/Pilot/Enemy contain only shared physical/health data. Pak subclasses can add local entity state. Motion reports collision normals without velocity, jump or wrapping policy. apply_damage() performs neutral health/protection arithmetic; hit_player()/hit_enemy() dispatch Pak damage policy. The host registers identities and removes dead enemies before invoking their death hooks once, permitting arbitrary Pak-created children.

ProjectileBase and EffectBase objects are implemented in external Paks. The host schedules their callbacks and prunes inactive objects; it never separately integrates a projectile or implements ricochet, piercing, seeking, explosion or return rules. Projectile/effect rendering also belongs to those objects. Obstacles supply their own health and presentation; there is no platform trait in core geometry.

Shared services provide geometry, asset/audio playback and basic rendering. Shared run rules remain the endless +1 initial-enemy sequence, defeat/clear state and clear/swap timing. Component callbacks own initial/swap protection, healing, rewards, spawn placement, aiming, defeat feedback and difficulty interpretation. Every level increments the level number, rebuilds fresh Pak-generated obstacle geometry, repairs pilot overlap, dispatches on_level_start, and spawns the initial enemies. on_level_complete runs once before the clear screen. on_shuffle runs after replacement and overlap repair, with the changed channels. Music/background swaps preserve locked actor instances and obstacle health; changing an actor component calls its factory while preserving only shared identity/position/health. Protected swaps clear projectiles.

## Partial Paks and discovery

Complete Paks cover all six types and support solo/coherent play. Partial Paks join only their provided pools. Enabled partials can collectively cover the required six types without any complete Pak. Coherent mode uses complete Paks; component remix uses eligible providers per unlocked channel. Automatic swaps require an actual alternative provider.

A component can inherit an installed provider's class with local filename overrides. It receives a fresh instance, with overridden load_asset() calls resolving locally and other assets staying at the provider. Missing/cyclic dependencies, unsupported APIs, invalid paths, abstract implementations and import/init errors become Pak status issues. Relative helpers use isolated namespaces and fresh-source rescans. Pak code is trusted local Python.

## Assets and persistence

ImageAsset handles decode lazily and can select SpriteFrame rectangles from grid sheets. SoundAsset handles play through the current run's effects bus. Loops are idempotent per handle; cleanup stops owned voices at pause/focus loss, intermissions, replacement, death and run end. Simulation-only worlds remain silent. Music streaming follows its own preference.

Core resources resolve from checkout/frozen/Python installation locations. Pak assets resolve inside their component folder (or an explicit installed-provider override). Windows builds keep all Pak folders beside the executable; wheels preserve them as external data under share/system-panic/paks. No credentials, generation service or network call is needed to play.

Preferences validate IDs/types, repair provider coverage, clamp values and save atomically. Schema 2 migrates old arena locks to background/obstacles and old pilot locks to music. Corrupt files recover to defaults; unavailable content shows an incomplete library rather than crashing. Source tests use temporary directories under output/test-temp.

Compatibility checks exercise all 1,296 gameplay-component mixtures and independently render/stream all 36 background/music pairs in the launch set. These are reported separately from the 46,656 possible six-channel selections. Headless checks establish behavior, not final human balance.

## Procedural content and level pressure

ObstaclesBase.build(world) is called at every level arrival, including solo play and locked obstacle channels, and when the provider changes mid-level. Each shipped generator seeds a private RNG with the run seed, its identity and world.wave. Combat history does not change the layout; repeated builds create equal geometry with fresh full-health objects. The generators keep their own room/debris/circuit/platform/hedge/orbital structure and bounded passage sizes.

Enemy components read world.wave in factories and active AI, and interpret the difficulty preference locally. Health and damage keep growing; movement and firing curves approach per-Pak limits. Later tactics include lead targeting, flanking, probing around cover, dash reflections and pursuing formations. Bullet damage is captured by its Pak when fired. Copying an enemy folder also copies its local tactics/bullet helpers; no launch rules live in the core.
