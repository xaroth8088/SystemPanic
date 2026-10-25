# Tooling memory

- `verify.py`: bounded samples of all six endless solo runs (12 cleared levels by default), verifying +1 initial enemy per level and continued play, plus UI screenshots and asset hashes. The QA stopping point is not a game finish.
- `compatibility.py`: full opening levels for every pilot/enemy/weapon/obstacle gameplay mix (6^4 with the launch set), plus rendering/streaming every background/music pair (6^2). The report distinguishes these checks from the full six-channel mix space.
- `build.py`: Windows folder build with production assets. Rebuild after runtime changes and smoke-test the executable from a different working directory.
- Windows builds copy discovered content folders to external `paks/` beside the executable. Never compile/import launch Pak modules into the engine. `setup.py` preserves the same external folder hierarchy for Python installations. Check a newly added Pak against an already built executable, partial-only mixes, and no-Pak startup.
- `verify_distribution.py`: frozen solo smoke checks, a new ID/code/helper added after build, partial-only gameplay, empty/invalid-install screenshots and wheel layout assertions. It creates/removes its own known probe folder in the ignored distribution. The source verification/compatibility runners accept repeated `--pak-dir` options for isolated authoring checks.
- `new_pak.py`: non-overwriting starter generator. Copies selected component folders/assets and records their source; supports complete and partial API 4 Paks. Add future authoring helpers here rather than making runtime depend on generation services.
- [Asset authoring](assetforge/AGENTS.md): separate from runtime, with recorded provenance.
- `assetforge/local.py` + `run_audio.bat`: isolated official Stable Audio 3 installation, local batch generation and loopback-only studio. Pinned upstream revision and tested dependency lock; models/cache are ignored. Never install these dependencies into the game runtime.

Generated reports, screenshots, test profiles and build products belong in ignored `output/`, `build/` and `dist/`. Keep concise verified results in the wiki.

`verify_levels.py`: 180 cases across five seeds and levels 1/2/7/12/50/101. Checks repeatable fresh geometry, separate RNG, bounds and safe actor placements; exercises one second of advanced AI and renders levels 1/2/12 for every Pak. No survival assertion is made for late-level stress samples.
