# Asset generation memory

This folder is a development pipeline; nothing here is imported by the game. No third-party art/music from the legacy prototypes is shipped in the revival.

## Providers
- Images: built-in imagegen. Save selected originals in `assets/images` and record prompts, provider and hashes in `assets/manifest.json`.
- Audio: Stability AI Stable Audio 3 via the official public Hugging Face Space (`stabilityai/stable-audio-3`), or a caller-specified compatible Gradio endpoint. Endpoint contract discovered 2026-10-24 at `/gradio_api/info`, named endpoint `/infer`: variant_key, prompt, duration, steps, cfg_scale, sampler_type, seed. Models: medium / small-music / small-sfx. Public quota/availability is outside our control. Never evade authentication or quota limits.
- Optional Stability API requires locally configured credentials; do not store secrets in the repository.

## Workflow
Keep prompt jobs in `prompts.json`. `audio.py` submits one explicit job at a time, downloads successful outputs, records source/model/seed/hash, and reports failures honestly. `prepare.py` performs deterministic production processing (normalization, trimming, looping/encoding) and records derivatives. The shipped game consumes only local prepared files.

## Discovery notes
Pinokio's configured control plane was unreachable on 2026-10-24; pterm search and localhost probes failed. A suitable official public Stable Audio 3 endpoint was discovered instead. Do not assume Pinokio is unavailable permanently.

## Delivered assets and processing

The user subsequently requested local installation and generation. The official Windows LiteRT runtime is installed under ignored `.asset-tools/audio-env`, with the upstream checkout pinned to `77e0398c26f7d22d801ec1bb036307e8b231f741`. Models/cache are also under `.asset-tools`, separate from game dependencies. All six music tracks and all six effects were regenerated locally into `assets/audio/local`. Mastering prefers those files. Initial cloud sources remain for provenance; the old derived menu click is superseded in production.

`local.py install` creates the isolated environment and warms music/SFX models. `local.py generate --job all --offline` uses only cached weights. `run_audio.bat` / `local.py serve` starts the separate browser studio, bound to 127.0.0.1:7871 with sharing and telemetry disabled. Offline API checks generated fresh 1s SFX and 4s music files at 44.1kHz stereo in about four seconds each. Gradio receives PCM arrays rather than probing known WAVs with optional ffprobe.
Six music tracks and five effect sources were generated with Stable Audio 3. Public anonymous quota stopped after three tracks; an existing local legacy Hugging Face token file enabled the remaining jobs. Do not record that token. The final `select` job hit authenticated quota; the shipped menu confirmation is an explicitly recorded 120ms excerpt from the generated `clear` chime, not a claimed new generation.

The atlas and title image came from built-in imagegen. The actual atlas row bands differ from the requested equal grid: `(0,310)`, `(310,565)`, `(565,805)`, `(805,1024)`. Renderer metadata slices these bands, trims 14 pixels from column edges and fits visible content without modifying the source pixels/alpha.

Following the dynamic Pak reorganization, `export_paks.py` now performs that same lossless crop/trim outside the game and saves four individual sprites plus an unmodified mastered music copy under each launch Pak's local assets. The runtime has no atlas column assumptions. Re-export after mastering or replacing the original atlas, then run `manifest.py`; `assets/pak-exports.json` records the derivatives. New Paks should own their independent source/production assets rather than extending the shared source atlas.

API 2 stores those exports directly in pilot/enemy/weapon/music/background/obstacles folders. There are 48 recorded derivatives: four sprite crops, a resized original AI title for local scenery, music and two unmodified generated effect copies per Pak. The runtime loads handles through the component ABC API; it never exports or generates assets.

On this Windows environment, libsndfile's long Vorbis encoding overflowed its stack. `prepare.py` uses PCM IO plus installed FFmpeg for Vorbis; without FFmpeg it writes mastered WAV. Production outputs live under `assets/audio/production`. `manifest.py` validates source/derivative hashes. No generation code or credential loading enters the runtime or Windows build.

## Classic-inspired expansion
Six separate original transparent sprite sheets were generated with built-in imagegen and saved in assets/images/<pak>-source.png. Exact prompts/actual geometry are in image-prompts.json. Requested 1024 squares arrived as 1280 squares; alpha-island bounds grouped by quadrant preserve sprites extending slightly past cell lines. export_expansion.py records lossless component crops, prepared decorative background mosaics and unmodified mastered audio copies in pak-exports.json. export_paks.py preserves records owned by other exporters.

Eighteen additional local Stable Audio 3 jobs (six 24-second music tracks, six launch sounds, six specials) used cached models offline. The local ledger now has 30 successful jobs; production has 30 decodable sounds/tracks. The manifest records 176 sources/derivatives, including 96 role-local exports across twelve Paks. These counts are verified by the asset tests; generation remains separate from runtime.
