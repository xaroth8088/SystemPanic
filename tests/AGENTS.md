# Verification memory

Use real simulation tests for solo play, all pairings/full component combinations, shuffle state preservation, preferences validation/persistence, projectile ownership, damage, endless level progression, death/restart and menu input. Run with SDL dummy video/audio in automation. Do not require network or asset generation for tests.

`tools/verify.py` should produce reproducible screenshots and a machine-readable report. Inspect the screenshots in addition to checking assertions. Record exact results here after running. Interactive playtesting remains distinct from headless simulation.

Earlier verification snapshots below describe the original finite implementation. The endless progression results at the end supersede their eight-wave finish and enemy counts.

## Verified 2026-10-24
- Python 3.12.1 / Pygame 2.6.1: 17 tests pass, including local asset hashes and decoding all twelve production audio files.
- Seed 24, relaxed difficulty: all six solo Paks complete all eight waves through ordinary deterministic controls. Completion times: Signal Runner 79.22s, Void Drifter 143.35s, Iron Circuit 100.12s, Sky Forge 74.47s, Phase Garden 57.02s, Orbit Keeper 101.75s.
- All 1,296 component mixtures clear a full opening wave with ordinary controls (seed 24, relaxed; worst case 44.18s). Component smoke tests, state preservation, collision recovery, pause/focus loss, restart, enabled selection and preference corruption are also covered.
- Screenshots inspected for library, settings, help and representative gameplay. Generated atlas slicing, header overlap, screen-edge clipping and menu text contrast were corrected during review.
- Fresh local Studio API generations: 1s SFX and 4s music, seed 742, 44.1kHz stereo, model downloads disabled. Both succeeded in about four seconds. All twelve shipped source audio jobs were also generated locally.
- PyInstaller Windows folder build succeeds; packaged headless checks exercise every solo Pak from a different working directory. A Python wheel also builds.
- Desktop Computer Use launch was not completed: the tool timed out waiting for app approval. Native mouse/key behavior is covered by event-driven UI tests; do not call that a human playtest.

Reproducible reports/screenshots live in ignored `output/verification`; concise evidence is copied to `docs/verification.json`. Re-run relevant checks after changes; do not claim new coverage from old reports.

## Transition flow refinement (2026-10-24)
- User clarified that periodic swaps get only a brief glitch/pause, while completed levels keep a short cleared message. Swaps now pause for 0.25s with no text banner or readiness state; level clears show their message for 1s, then start the next level directly. The initial new-run introduction remains.
- 19 tests pass, including new behavioral checks that swaps freeze combat only during the glitch, held input resumes automatically, and level-clear intermissions do not add a glitch or ready step.
- Rendered and inspected `output/transition-check/level-cleared.png`, `swap-glitch.png`, and `next-level.png`.
- All six full solo runs again reach victory with ordinary demo controls (seed 24, relaxed): 61.98s, 118.60s, 82.28s, 60.35s, 42.23s, 111.20s in registry order. The earlier Orbit Keeper demo policy lost late in the final wave after the timing change; its demo-only controller now steers away from imminent threats. Manual player controls and combat balance were not changed.

## Endless progression (2026-10-24)
- Progression now starts at one enemy and adds exactly one initial enemy per level, with no level cap or victory finale. Per-enemy health/speed scaling and Pak-specific fragments still apply. Old finite-run preferences cannot stop a run and are removed on save.
- 23 tests pass. Tests check every Pak's initial counts and direct continuation through level 21, growth at levels 99–101, ignored legacy preferences, and the absence of a finite-run setting. Existing transition, input, damage and compatibility checks still pass.
- All six solo Paks cleared twelve levels and continued into level thirteen with ordinary demo controls (seed 24, relaxed). Initial enemy counts were exactly 1–13. Sample times in registry order: 66.17s, 137.72s, 98.17s, 66.25s, 48.02s, 157.77s. Twelve cleared levels is a bounded QA sample, not a game ending.
- All 1,296 component mixtures cleared their opening level with ordinary controls (seed 24, relaxed; worst case 15.27s).
- Inspected new preferences, gameplay/level-cleared, and game-over screenshots. The HUD reads `LEVEL nn / ENDLESS`; settings explain 1, 2, 3... enemies. Level clears retain their one-second message; periodic swaps retain their quarter-second glitch only.
- Rebuilt the Windows distribution and Python wheel. All six packaged Paks passed 240-frame headless smoke checks from a different working directory; the refreshed Windows ZIP passed its archive integrity check. Current build hashes and results are recorded in `docs/verification.json`.

## Dynamic and partial Paks (2026-10-24)
- The six launch Paks now load from external folders through manifest API 1. No launch Pak IDs, atlas geometry or behavior branches remain in the core. New Pak code/assets do not require rebuilding the executable.
- 33 tests pass. Added coverage includes a new complete Pak with the launch set absent; complementary partial-only play; per-channel eligibility; solo/coherent exclusion of partials; asset-only inheritance; missing/cyclic dependencies; duplicate/malformed/escaped-path/import-error isolation; separate helper namespaces; same-timestamp entry/helper rescans; preference repair; paginated libraries; incomplete/empty installs; and coverage-preserving selection. A same-timestamp helper test exposed stale bytecode and passed after fresh-source loading was added.
- Automatic swaps now require a genuine alternative in an eligible unlocked pool. Four partial Paks supplying exactly one provider per component remain locked without redundant glitches. Existing level-clear and swap timing checks pass.
- All six dynamically loaded solo games again cleared twelve levels and continued into level thirteen (seed 24, relaxed). All 1,296 eligible component mixtures cleared their opening level; worst case 15.27s.
- Rebuilt Windows executable: all six launch games passed 240-frame smoke checks. A new Pak and relative helper added beside the already built executable were executed successfully, with its new ID selected solo. Four complementary partial Paks also ran and fired through the frozen executable with no complete Paks available. Empty installs and broken-Pak status screens rendered successfully. These checks are reproducible with `python tools/verify_distribution.py` after building the executable and wheel.
- The wheel contains only loader/API modules in the core Pak package; all six game folders and assets are external data. Installed it into a fresh Python prefix and ran 240 frames with all six external Paks and their assets discovered from that installation.
- Inspected default library/status, partial-only library/gameplay, empty-install and invalid-Pak screenshots. Current evidence is in `docs/verification.json`; screenshots and detailed logs remain under ignored `output/verification`.

## Component folders and ABC API 2 (2026-10-24)
- All six launch Paks use pilot/enemy/weapon/music/background/obstacles folders. Code and local assets live together. The public API is six ABCs in `src/system_panic/pak_api.py`; private handle attribute names are not API. API 1 flat modules are superseded.
- 45 tests pass. Coverage includes required abstract methods/base types, init-time file validation, preview/track handle validation, animation frame rectangles, class export/folder discovery, per-world state/handle isolation, inherited local filename overrides, music-only partials, independent presentation channels, real mixer loop idempotence/volume and pause/replacement/end cleanup. A starter generator creates complete and partial Paks without overwriting. Legacy locks migrate to preference schema 2.
- Tests also verify that bounded runs and Quit events release component instances exactly once, without another update reactivating them during shutdown.
- All six solo games cleared twelve levels and continued into level thirteen (seed 24, relaxed). All 1,296 gameplay mixes cleared a level (worst 17.50s); all 36 background/music pairs rendered/streamed without advancing gameplay/RNG. These are separate checks, not 46,656 full gameplay runs.
- Source library/settings/HUD screenshots inspected: six independent channels are visible and fit the canvas. Public API and loader IDE diagnostics report zero problems. Original AI provenance covers all 48 component-local exports/copies; assets remain generated outside the game.
- Fresh Windows build passes all six solo smoke checks, an ABC-based Pak/helper added after the executable was built, and a six-partial-only mix. Empty/invalid installations still render. Frozen partial library/gameplay screenshots inspected; source-format layout assertions reject old flat pak.py/assets folders in the folder build and wheel.
- Installed the fresh wheel into a new Python prefix and played 240 frames with six structured external Paks. The Windows ZIP was refreshed and integrity-checked; current hashes and detailed evidence are in `docs/verification.json`.
