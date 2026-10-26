# Design memory

## Identity
System Panic is about adapting when familiar arcade rules change in an ongoing battle. A brief corruption transition communicates the shuffle. Coherent Paks establish learnable rules; component remix creates surprising combinations. Prefer readable chaos, generous invulnerability on swaps, and understandable controls.

Flow clarification (2026-10-24): periodic randomization uses only a quarter-second visual glitch and automatically resumes. Level completion has a separate one-second "level cleared" message before the next level. Do not append a readiness screen or glitch to that level change; the initial new-run introduction is separate.

## Launch scope
Twelve Paks share arena coordinates, damage, rewards and level objectives, but own distinct locomotion, weapon, enemy behavior and arena layout. Progression is always endless: level one starts with one enemy, level two with two, and so on until defeat. No scripted elite waves, finale, finite-run toggle or level cap. The short level-cleared message, score, death and restart remain.

Content is dynamically loaded from external folders. All twelve shipped Paks use the same manifest API as added Paks. Complete Paks support solo/coherent play; partial Paks supply any subset of six components for remix. Asset-only partials may inherit installed behavior. The enabled pool needs all six channels, but can be made entirely from complementary partial Paks. See [the format guide](paks.md).

## Architectural choices
- New implementation; the removed historical source and assets remain in Git history. See [prototype history and credits](history.md).
- Desktop Python/Pygame keeps installation modest and the game offline.
- API 4 is defined by PilotBase, EnemyBase, WeaponBase, MusicBase, BackgroundBase and ObstaclesBase. Component classes and their assets live together in role folders. Frozen catalog definitions create fresh, run-owned instances. Mutable handles/counters belong to those instances and engine state belongs to World.
- Catalogs are discovered before preferences and passed through runtime services. Library rescans replace catalogs outside active runs. UI pagination and empty/invalid-install handling are part of the contract; do not assume six installed entries.
- Shared state across shuffles is deliberately small. Health, score, wave, shared positions and enemy health survive; a Pak may constrain its adopted position to its locomotion domain. Movement/AI-specific transient state is reinitialized.
- Complete Paks work alone. Awkward or ineffective mixed combinations are acceptable until a periodic swap; do not grant restricted pilots extra movement or force every weapon to reach every enemy. Obstacle durability belongs to its Pak, including impervious geometry.

## Delivery state

Static Remix adds a separate library entry for choosing all six providers and playing without periodic changes. Named favorites can be saved as new copies, renamed and deleted, or captured from an active run through Pause → Save Current Mix. Missing Pak references remain visible and manageable. Favorites launch fresh endless runs, with procedural terrain still regenerated each level; they are not session saves. See [runtime memory](../src/system_panic/AGENTS.md) and the current verification snapshot for tested details.
Delivered implementation on `codex/revival`: twelve complete Paks, solo/coherent/component modes, endless +1 enemy progression, local preferences and high scores, UI/help/credits, protected shuffles and original audiovisual assets. The obsolete 2017/2025 prototypes and their unused media were removed from the working tree on 2026-10-25; Git history retains them, and [historical credits](history.md) remain in the current documentation.

Stable Audio 3 is installed separately under ignored `.asset-tools`, with a pinned official Windows LiteRT backend and dependency lock. Twelve soundtracks and eighteen effects were generated locally and mastered for production. The expansion adds six original AI sprite sheets and eighteen local audio generations. Fresh music and SFX were also generated through the local studio API with Hugging Face downloads disabled. The studio is loopback-only; the game never calls it.

See [verification memory](../tests/AGENTS.md) and `docs/verification.json` for evidence. Input supports keyboard/mouse and SDL-mapped gamepads, including every menu. Preferences include a deadzone/controller page; custom remapping remains future work. Automated runs establish playability, not final human balance. No online catalog was built.

Level refinement: Paks now own spawn/aim/difficulty, protection/healing/rewards and defeat feedback. Layouts procedurally regenerate each level (also solo/locked), with separate seeded RNGs and distinct Pak shapes. Enemy difficulty includes new tactics as well as numerical scaling; shared +1 progression and transitions retain their contract.

The six additional Paks use original AI artwork/audio and classic-inspired mechanics: Breakout (perimeter paddle/multiball), Pac-Man (buffered turns/chomp/chase-scatter), Dig Dug (excavation/inflation), Qix/Tron (right-angle movement/closed-tail captures), Space Invaders (bottom-line horizontal movement/salvos/formations), Frogger (lane hopping/traffic/harpoons). Each is complete and its six components can be copied independently. No game-specific rules were added to the host.

Orbit Keeper's special also toggles explicit inward/outward radial fire. Optional PilotBase.aim_direction/status queries are additive to API 4; weapons decide how to respect pilot intent and the shell displays the status string. Nearest-target assistance and guided flight must not override an explicit pilot direction. Glaive outbound speed is now 600 so radial fire and constrained mixed pilots can reach the arena edge. Demo input policies were updated to line up radial shots and avoid crowds; they use ordinary controls only.


Latest refinement: every tenth enemy destroyed drops a weapon-local collectible. All twelve weapons scale with the run-wide collected count, which persists across swaps/levels. Existing generated weapon art supplies local pickup icons; no generation service runs in the game. See the README upgrade table and API examples.

Terrain now includes permanent Signal/Phase/Sky geometry, connected jump arrangements, projectile-transparent oval/chicane racetracks, gravitational wells and crossing comets. Vector closed tails carve solid interiors with walkable borders and enemy-only live-line collisions; the weapon owns their lifetime. Maze normal attacks are forward dash/contact knockbacks, Burrow has finite reach, Orbit uses ring steps and offscreen returning glaives, Neon ignores vertical input, and Star shots expire at bounds. Human balance remains separate from bounded QA samples.

Expansion audio repair: all twelve short launch/special effects were regenerated locally after reproducing faulty fractional-duration conditioning in the pinned LiteRT backend. The generator now requests whole seconds and the mastering tool trims the final effects. Existing music/common effects remain unchanged. Provenance and quality-regression evidence live in [asset generation memory](../tools/assetforge/AGENTS.md).
