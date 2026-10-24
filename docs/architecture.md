# Runtime and Pak architecture

`App` owns window lifecycle, menus, preferences, input and local audio playback. `World` owns fixed-step simulation, combat, safe placement, waves and shuffle transitions. `Graphics` draws without advancing state. `tools/assetforge` is a separate authoring pipeline.

Simulation advances at 120 steps per second with an accumulator. Pausing, focus loss and settings do not consume gameplay time. Movement, damage and cooldowns use simulation seconds. Presentation randomness does not affect the seeded gameplay RNG.

Progression is always endless. Level n starts with n normal enemies, starting at one; there is no eight-level finish, scripted elite-wave override or finite-run preference. Existing enemy health/speed scaling and Pak-specific mid-level spawns still apply. Defeat is the only terminal gameplay state. Legacy `endless` preference keys are ignored and removed on the next save.

## A complete Pak

Game content lives in external `paks/<id>/` folders. `pak.json` declares API version, components, metadata, local sprite/music paths and an optional Python entrypoint. The core's `system_panic.paks` package contains only the contract and discovery loader. Complete Paks supply all four channels; partial Paks supply any nonempty subset and join only their eligible channel pools. Asset-only variants may inherit installed component behavior. See [the full Pak guide](paks.md) and [authoring memory](../paks/AGENTS.md).

`discover(roots)` returns an immutable catalog of loaded definitions and isolated loader issues. Catalogs are passed to the shell, preferences, simulation, renderer and audio. Startup and library rescans discover folders; the executable has no static list of game content. Missing/cyclic dependencies, unsupported APIs, duplicate IDs, missing local assets/callbacks and import failures appear in Pak status. Relative helpers use separate package namespaces and fresh-source loading. Local Pak code is trusted Python, not sandboxed code.

Movement, firing, enemy AI and arena geometry are dispatched through their component's callbacks. Pilot initialization, arena decoration and demo policies also belong to Paks. Sprite presentation is generic metadata; the renderer has no launch-game names, behavior branches or shared-atlas columns. Projectile capabilities (piercing, ricochets, seeking, area damage, returning), collision and damage remain shared engine services.

## Shuffle invariants

Configurations map `pilot`, `weapon`, `enemy` and `arena` to Pak IDs. Solo fixes them to one complete Pak. Coherent mode selects an enabled complete Pak. Component remix selects enabled providers independently for each declared channel; locked channels keep their initial selection. Choices exclude the previous selection when alternatives exist.

Health, score, wave and enemy identity/health survive. Changing pilot creates clean locomotion state. Enemy callbacks receive clean timers/velocity. Cover is rebuilt; a bounded search repairs overlaps; both teams' shots are cleared; the player receives invulnerability. A brief corruption transition makes the new rules readable.

Periodic swaps remain in active mode: a 0.25s visual-only glitch freezes simulation, then held controls resume immediately. Level completion uses its own 1s cleared-message phase, followed directly by active play in the next level. Level changes do not create a glitch or another ready phase. Only a new run gets the initial ready introduction.

Destructible cover, long-range weapons and default aim assistance keep different movement models compatible. The compatibility runner verifies full opening waves across all combinations.

## Assets and persistence

Core assets resolve from the checkout, frozen bundle or Python installation. Pak assets resolve inside their own external folders. Standalone builds keep `paks/` beside the executable; Python distributions preserve the same tree under `share/system-panic/paks`. Raw AI generations remain for provenance; the build ships exported local sprites/music in each Pak plus shared title/effects. Runtime has no generation SDK, credential loading or HTTP code.

Preferences validate IDs/types, clamp numbers, repair missing providers after Pak removal and prevent a mix with missing component coverage and save atomically. Corrupt files recover to defaults; save errors do not prevent play. Sandbox tests use temporary directories under `output/test-temp`, because the execution sandbox can deny atomic renames in the OS temporary directory.
