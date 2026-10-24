# Verification memory

Use real simulation tests for solo play, all pairings/full component combinations, shuffle state preservation, preferences validation/persistence, projectile ownership, damage, victory/death/restart and menu input. Run with SDL dummy video/audio in automation. Do not require network or asset generation for tests.

`tools/verify.py` should produce reproducible screenshots and a machine-readable report. Inspect the screenshots in addition to checking assertions. Record exact results here after running. Interactive playtesting remains distinct from headless simulation.

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
