# System Panic memory map

This is the entry point to the project's agent wiki. Read the relevant linked page before changing a subsystem; update that page with durable decisions, verified facts, and unresolved issues when finishing work. Keep memory near the code, link instead of duplicating, and distinguish intentions from tested behavior.

## Product contract
- A single-player offline arcade remix game. Complete Paks work alone; partial Paks supply any nonempty subset of pilot, enemy, weapon, music, background and obstacles for the mix. An enabled mix must cover all six channels.
- Game content is discovered from external Pak folders, never imported from a fixed content registry. The public ABCs in `src/system_panic/pak_api.py` define the API; each component folder owns its class and local assets. The core owns loading, scheduling, neutral primitives and shared run flow. Gameplay rules belong to Paks; no family/splitting/cooldown or projectile-feature traits are interpreted by the host. Asset-only partial Paks may inherit installed component behavior.
- Progression is always endless: level one starts with one enemy, and each new level adds exactly one initial enemy. There is no finale, level cap, finite-run preference or scripted boss-wave replacement. Pak-specific mid-level spawning (such as asteroid fragments) remains part of that Pak's mechanics.
- The platform arena is one Pak, not the overall design direction.
- Twelve complete Paks. Original six: Signal Runner, Void Drifter, Iron Circuit, Sky Forge, Phase Garden, Orbit Keeper. Classic-inspired expansion: Neon Breach, Maze Muncher, Burrow Patrol, Vector Coil, Star Bastion, Tide Hopper.
- Players can select enabled Paks, solo/coherent/component remix, shuffle interval, difficulty, effects, fullscreen, rendering output resolution and audio levels. No online catalog.
- Original generated art and audio are produced by development tools, never generated or downloaded by the game.

## Wiki
- [Design and delivery state](docs/AGENTS.md)
- [Runtime and state invariants](src/system_panic/AGENTS.md)
- [Pak authoring and compatibility](paks/AGENTS.md)
- [Asset generation and provenance](tools/assetforge/AGENTS.md)
- [Verification](tests/AGENTS.md)
- [Project history and prototype credits](docs/history.md)

## Working conventions
- Active implementation is `src/system_panic`; removed prototypes and their assets remain in Git history only. See [project history](docs/history.md).
- Python 3.12+, Pygame, fixed simulation step, seeded local RNG. No mandatory network or generation credentials at runtime.
- Use `python play.py`, `python -m unittest discover -s tests -v`, and `python tools/verify.py` from the root. Windows `run.bat` manages a local environment.
- Before claiming completion, run meaningful tests and inspect rendered screens. Record exact evidence and remaining limitations in the wiki.
- Do not fabricate asset provenance or mark pending generation as delivered.

- Every level regenerates obstacle geometry, including solo play and locked obstacle channels. Paks own procedural layout rules and level-based difficulty, including spawn/aim/protection/healing/reward policy. See API 4 and the nearby runtime/Pak memories.
- Awkward or ineffective component combinations are allowed: periodic swaps are part of the game. Complete Paks must still work independently. Do not force every possible mix to clear, grant incompatible pilots extra movement, or make every obstacle destructible.
- SDL-mapped gamepads support gameplay and menu navigation through the same Controls contract. Stick input selects the same eight digital directions as the D-pad, with no analog speed or steering. Input devices, mappings, menu focus, deadzones and disconnect/focus safety belong to the shell; do not add controller-specific rules to Paks.

- Every tenth destroyed enemy asks the active weapon to create a Pak-owned PowerupBase at the death position. Each weapon folder owns powerup.py and interprets world.powerups_collected; pickups/upgrades survive weapon and level changes. Motion/pickup/expiry/formulas stay in Paks.
- Components may register owned geometry through world.set_geometry/clear_geometry. Shape callbacks own filtering/presentation/responses; the host provides collision scheduling and automatic cleanup on replacement.
