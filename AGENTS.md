# System Panic memory map

This is the entry point to the project's agent wiki. Read the relevant linked page before changing a subsystem; update that page with durable decisions, verified facts, and unresolved issues when finishing work. Keep memory near the code, link instead of duplicating, and distinguish intentions from tested behavior.

## Product contract
- A single-player offline arcade remix game. Every Pak must be a complete playable game alone; independently shuffling pilot, weapon, enemy family and arena must remain playable.
- Progression is always endless: level one starts with one enemy, and each new level adds exactly one initial enemy. There is no finale, level cap, finite-run preference or scripted boss-wave replacement. Pak-specific mid-level spawning (such as asteroid fragments) remains part of that Pak's mechanics.
- The platform arena is one Pak, not the overall design direction.
- Six launch Paks: Signal Runner, Void Drifter, Iron Circuit, Sky Forge, Phase Garden, Orbit Keeper.
- Players can select enabled Paks, solo/coherent/component remix, shuffle interval, difficulty, effects, fullscreen and audio levels. No online catalog.
- Original generated art and audio are produced by development tools, never generated or downloaded by the game.

## Wiki
- [Design and delivery state](docs/AGENTS.md)
- [Runtime and state invariants](src/system_panic/AGENTS.md)
- [Pak authoring and compatibility](src/system_panic/paks/AGENTS.md)
- [Asset generation and provenance](tools/assetforge/AGENTS.md)
- [Verification](tests/AGENTS.md)
- [Historical prototypes](legacy/AGENTS.md)

## Working conventions
- Active implementation is `src/system_panic`; do not import from `legacy`.
- Python 3.12+, Pygame, fixed simulation step, seeded local RNG. No mandatory network or generation credentials at runtime.
- Use `python play.py`, `python -m unittest discover -s tests -v`, and `python tools/verify.py` from the root. Windows `run.bat` manages a local environment.
- Before claiming completion, run meaningful tests and inspect rendered screens. Record exact evidence and remaining limitations in the wiki.
- Do not fabricate asset provenance or mark pending generation as delivered.
