# Design memory

## Identity
System Panic is about adapting when familiar arcade rules change in an ongoing battle. A brief corruption transition communicates the shuffle. Coherent Paks establish learnable rules; component remix creates surprising combinations. Prefer readable chaos, generous invulnerability on swaps, and understandable controls.

Flow clarification (2026-10-24): periodic randomization uses only a quarter-second visual glitch and automatically resumes. Level completion has a separate one-second "level cleared" message before the next level. Do not append a readiness screen or glitch to that level change; the initial new-run introduction is separate.

## Launch scope
Six Paks share arena coordinates, damage, rewards and level objectives, but own distinct locomotion, weapon, enemy behavior and arena layout. Progression is always endless: level one starts with one enemy, level two with two, and so on until defeat. No scripted elite waves, finale, finite-run toggle or level cap. The short level-cleared message, score, death and restart remain.

Content is dynamically loaded from external folders. The six launch Paks use the same manifest API as added Paks. Complete Paks support solo/coherent play; partial Paks supply any subset of components for remix. Asset-only partials may inherit installed behavior. The enabled pool needs all four channels, but can be made entirely from complementary partial Paks. See [the format guide](paks.md).

## Architectural choices
- New implementation, historical source archived under `legacy/`.
- Desktop Python/Pygame keeps installation modest and the game offline.
- Data and behavior are separate: frozen Pak definitions select explicit behavior functions; mutable world state belongs to the engine.
- Catalogs are discovered before preferences and passed through runtime services. Library rescans replace catalogs outside active runs. UI pagination and empty/invalid-install handling are part of the contract; do not assume six installed entries.
- Shared state across shuffles is deliberately small. Health, score, wave, entity positions and enemy health survive; movement/AI-specific transient state is reinitialized.
- All weapons can reach enemies across the screen; destructible cover and safe relocation prevent incompatible mixtures from trapping the player.

## Delivery state
Delivered implementation on `codex/revival`: six complete Paks, solo/coherent/component modes, endless +1 enemy progression, local preferences and high scores, UI/help/credits, protected shuffles and original audiovisual assets. Historical prototypes are preserved under `legacy`.

Stable Audio 3 is installed separately under ignored `.asset-tools`, with a pinned official Windows LiteRT backend and dependency lock. Six soundtracks and six effects were generated locally and mastered for production. Fresh music and SFX were also generated through the local studio API with Hugging Face downloads disabled. The studio is loopback-only; the game never calls it.

See [verification memory](../tests/AGENTS.md) and `docs/verification.json` for evidence. Current input is keyboard/mouse; gamepad support and remapping remain future work. Automated runs establish playability, not final human balance. No online catalog was built.
