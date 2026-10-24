# Asset memory

See [generation memory](../tools/assetforge/AGENTS.md). `manifest.json` indexes provenance. Full prompts live with the authoring tools. `images/` contains two imagegen outputs; `audio/*.wav` preserves initial cloud generations and the initial derived menu click; `audio/local/*.wav` contains all twelve local generations. `audio/production/` contains the mastered local outputs used by the game.

Do not silently substitute third-party assets or procedural placeholders for recorded AI outputs. Verify hashes with `tools/assetforge/manifest.py` after changes. Runtime and standalone builds use local files without generation services or credentials.
