# External Pak memory

Read [the root wiki](../AGENTS.md), [format and installation guide](../docs/paks.md) and [runtime architecture](../docs/architecture.md). This folder is game content, separate from the engine's Python package. Every child folder with `pak.json` is discovered dynamically; no registration edit or game rebuild is needed.

## Contracts
- A complete Pak declares all four `components`: pilot, weapon, enemy, arena. It can play solo or join coherent/component shuffle.
- A partial Pak declares any nonempty subset. It joins only its declared component pools and never offers solo play. A mix made solely of partial Paks is valid if they collectively cover all four channels. Coherent shuffle selects complete Paks only.
- Each supplied component has a local sprite. Music is optional and follows the selected pilot. Asset-only variants use per-component `inherits` references to installed Pak IDs; missing or cyclic dependencies are reported and skipped.
- Behaviors use engine-owned positions, velocity, health and IDs. Cover is destructible and every weapon needs enough reach to handle every enemy family. Keep spawn/relocation bounded. Opaque state cannot survive a component change.
- `move`, `fire`, `advance_enemy`, and `make_arena` belong to their respective components. `prepare_pilot`, `draw_arena` and `demo_controls` are optional Pak callbacks. Rendering must not advance simulation or consume gameplay RNG.
- Local helper modules use relative imports. Depend on the core API, Pygame and modules available in the runtime; standalone builds do not install arbitrary third-party dependencies for Paks.
- Preserve original AI provenance. `tools/assetforge/export_paks.py` derives the launch sprites losslessly from the recorded atlas and copies mastered music; `assets/pak-exports.json` and `assets/manifest.json` record hashes.

All six launch Paks remain complete and distinct. Each Pak's nearby `AGENTS.md` records its identity. Test complete Paks alone, partial Paks in channel-valid mixes, and enabled/disabled selection after installation/removal. The core owns endless +1 enemy progression and the established transition timing.
