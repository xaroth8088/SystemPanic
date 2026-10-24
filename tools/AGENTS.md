# Tooling memory

- `verify.py`: bounded samples of all six endless solo runs (12 cleared levels by default), verifying +1 initial enemy per level and continued play, plus UI screenshots and asset hashes. The QA stopping point is not a game finish.
- `compatibility.py`: full opening waves across all 6^4 mixtures.
- `build.py`: Windows folder build with production assets. Rebuild after runtime changes and smoke-test the executable from a different working directory.
- [Asset authoring](assetforge/AGENTS.md): separate from runtime, with recorded provenance.
- `assetforge/local.py` + `run_audio.bat`: isolated official Stable Audio 3 installation, local batch generation and loopback-only studio. Pinned upstream revision and tested dependency lock; models/cache are ignored. Never install these dependencies into the game runtime.

Generated reports, screenshots, test profiles and build products belong in ignored `output/`, `build/` and `dist/`. Keep concise verified results in the wiki.
