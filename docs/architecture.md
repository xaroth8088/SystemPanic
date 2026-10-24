# Runtime and Pak architecture

`App` owns window lifecycle, menus, preferences, input and local audio playback. `World` owns fixed-step simulation, combat, safe placement, waves and shuffle transitions. `Graphics` draws without advancing state. `tools/assetforge` is a separate authoring pipeline.

Simulation advances at 120 steps per second with an accumulator. Pausing, focus loss and settings do not consume gameplay time. Movement, damage and cooldowns use simulation seconds. Presentation randomness does not affect the seeded gameplay RNG.

## A complete Pak

Each module under `src/system_panic/paks` owns four callbacks plus metadata:

```python
def move(world, dt, control, jump, special): ...
def fire(world, direction): ...
def advance_enemy(world, enemy, dt): ...
def make_arena(): ...  # list[Cover]

PAK = Pak(..., move=move, fire=fire, advance_enemy=advance_enemy,
          make_arena=make_arena, cooldown=0.25, splits=0)
```

`move` updates the engine-owned pilot using shared collision helpers. `fire` uses `world.spawn_shot`, `world.damage_enemy` and/or `world.beams`. `advance_enemy` implements its AI; the engine already advances age and timer. `make_arena` returns fresh destructible cover. The engine dispatches the independently selected Pak's callback for each channel; adding a Pak does not require another behavior branch in the engine.

Shared projectile capabilities include piercing, ricochets, seeking, area damage and returning to the owner. The engine advances each projectile once and owns damage, hit ownership and cleanup.

Register the exported definition in `paks/registry.py`, provide original assets, update the wiki, and test alone and with current components. Pak code is trusted local Python. The game does not fetch or execute remote Paks.

## Shuffle invariants

Configurations map `pilot`, `weapon`, `enemy` and `arena` to Pak IDs. Solo fixes them to one Pak. Coherent mode selects a complete Pak. Component remix selects enabled channels independently; locked channels keep their initial selection. Choices exclude the previous selection when alternatives exist.

Health, score, wave and enemy identity/health survive. Changing pilot creates clean locomotion state. Enemy callbacks receive clean timers/velocity. Cover is rebuilt; a bounded search repairs overlaps; both teams' shots are cleared; the player receives invulnerability. A brief corruption transition makes the new rules readable.

Periodic swaps remain in active mode: a 0.25s visual-only glitch freezes simulation, then held controls resume immediately. Level completion uses its own 1s cleared-message phase, followed directly by active play in the next level. Level changes do not create a glitch or another ready phase. Only a new run gets the initial ready introduction.

Destructible cover, long-range weapons and default aim assistance keep different movement models compatible. The compatibility runner verifies full opening waves across all combinations.

## Assets and persistence

Paths resolve from checkout, frozen bundle or installed distribution, never the working directory. Raw AI generations remain for provenance; standalone builds ship only final images and mastered audio. Runtime has no generation SDK, credential loading or HTTP code.

Preferences validate IDs/types, clamp numbers, prevent an empty enabled set and save atomically. Corrupt files recover to defaults; save errors do not prevent play. Sandbox tests use temporary directories under `output/test-temp`, because the execution sandbox can deny atomic renames in the OS temporary directory.
