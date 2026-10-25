# Asset memory

See [generation memory](../tools/assetforge/AGENTS.md). `manifest.json` indexes provenance. Full prompts live with the authoring tools. `images/` contains the original atlas/title and six expansion imagegen outputs; `audio/*.wav` preserves initial cloud generations and the initial derived menu click; `audio/local/*.wav` contains thirty local jobs. `audio/production/` contains the mastered local outputs used by the game.

Do not silently substitute third-party assets or procedural placeholders for recorded AI outputs. Verify hashes with `tools/assetforge/manifest.py` after changes. Runtime and standalone builds use local files without generation services or credentials.

Launch Pak assets are exported into the role folders under each external `paks/<id>/`. `tools/assetforge/export_paks.py` reproduces the renderer's original lossless atlas crops and copies mastered music unchanged; `pak-exports.json` and the main manifest record all 48 exported hashes. Original sources stay here for authoring/provenance. Background images are resized derivatives of the recorded AI title; pilot/weapon clips are unmodified copies of existing generated effects. The core build ships the title and shared effects; it reads each Pak's sprites/music from that Pak's own folder.

Expansion assets add another 48 exports (96 total). The twelve expansion effects were regenerated on 2026-10-25 after finding fractional-duration inference produced sustained noise. Sources now retain whole-second inference; mastering trims onset/duration outside the game. Original music/common effects are unchanged. Previous source hashes/recipes remain in the local generation ledger and Git; current hashes point to the repaired files. Details and limitations are in the linked generation memory.
