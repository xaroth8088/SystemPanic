# Runtime and Pak architecture

App owns windows, menus, preferences, input and playback. World owns engine state and 120 Hz fixed-step simulation. Graphics draws without advancing state. tools/assetforge is a separate generation/export pipeline; the game only reads finished local assets.

Level n starts with n normal enemies. Play continues until defeat, with no finite-run toggle or finale. Existing health/speed scaling and Pak-specific fragments remain. Periodic swaps pause for a 0.25s visual glitch and resume held controls. Level clears show their message for one second and enter the next level directly; only a new run has the initial introduction.

## Definitions and instances

Content lives under external paks/<id>/ folders. Each role folder contains its class and assets: pilot, enemy, weapon, music, background and obstacles. The public contract is six ABCs in system_panic.pak_api. See [the complete guide and examples](paks.md).

pak.json declares API 2, display metadata and component selection/configuration. The loader validates and builds immutable ComponentSpec definitions (class, asset directory and optional overrides). Catalogs are passed to preferences, simulation, rendering and audio; there is no static launch-game registry.

World.component(channel) creates a run-owned instance with an asset context and optional audio service, then calls activate(world). init() loads local handles before world activation. Authors choose their own handle/counter attribute names; only explicit ABC methods/properties are API. World provides typed overloads for literal component names.

Instances remain while their selected provider stays unchanged. Replacements call deactivate/suspend, discard private state and instantiate fresh behavior. Worlds never share mutable component state. Preview objects are separate instances with no world/audio service.

## Component responsibilities

PilotBase moves engine-owned pilot state; EnemyBase advances enemy behavior after engine timers; WeaponBase creates projectiles/beams through shared helpers. ObstaclesBase builds fresh Cover collision geometry. BackgroundBase draws scenery without changing state or RNG. MusicBase chooses the track for the separate streaming bus. The renderer asks sprite() for a handle/frame and optional transforms, without looking up private fields.

Shared services own collision, safe placement, damage, projectile advancement/ownership, invulnerability, score and progression. Music/background swaps preserve locked pilot/enemy instances and obstacle health. Changing pilot resets locomotion state; changing enemy resets enemy behavior state while preserving identity/health; changing obstacles rebuilds cover and repairs overlaps. Protected swaps clear projectiles.

## Partial Paks and discovery

Complete Paks cover all six types and support solo/coherent play. Partial Paks join only their provided pools. Enabled partials can collectively cover the required six types without any complete Pak. Coherent mode uses complete Paks; component remix uses eligible providers per unlocked channel. Automatic swaps require an actual alternative provider.

A component can inherit an installed provider's class with local filename overrides. It receives a fresh instance, with overridden load_asset() calls resolving locally and other assets staying at the provider. Missing/cyclic dependencies, unsupported APIs, invalid paths, abstract implementations and import/init errors become Pak status issues. Relative helpers use isolated namespaces and fresh-source rescans. Pak code is trusted local Python.

## Assets and persistence

ImageAsset handles decode lazily and can select SpriteFrame rectangles from grid sheets. SoundAsset handles play through the current run's effects bus. Loops are idempotent per handle; cleanup stops owned voices at pause/focus loss, intermissions, replacement, death and run end. Simulation-only worlds remain silent. Music streaming follows its own preference.

Core resources resolve from checkout/frozen/Python installation locations. Pak assets resolve inside their component folder (or an explicit installed-provider override). Windows builds keep all Pak folders beside the executable; wheels preserve them as external data under share/system-panic/paks. No credentials, generation service or network call is needed to play.

Preferences validate IDs/types, repair provider coverage, clamp values and save atomically. Schema 2 migrates old arena locks to background/obstacles and old pilot locks to music. Corrupt files recover to defaults; unavailable content shows an incomplete library rather than crashing. Source tests use temporary directories under output/test-temp.

Compatibility checks exercise all 1,296 gameplay-component mixtures and independently render/stream all 36 background/music pairs in the launch set. These are reported separately from the 46,656 possible six-channel selections. Headless checks establish behavior, not final human balance.
