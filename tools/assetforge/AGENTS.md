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

## Short-effect repair (2026-10-25)
- The twelve expansion effects were valid files containing faulty generated audio, not damaged OGG containers. The pinned LiteRT backend reproduces the shipped Neon .8-second source byte-for-byte, while the same prompt/seed at 1 second yields a clean transient. All .8/1.2-second expansion jobs had sustained noise. Hash/decodability checks alone missed this quality failure.
- local.render now rounds inference duration up to whole seconds, validates the generated PCM and replaces the destination only after successful generation. Keep the full 1/2-second source; prepare.py removes quiet lead-in before limiting the final one-shot to the job duration and adding fades. Studio durations are already whole seconds. The game never performs this processing.
- Regenerated only those twelve effects offline using the original prompts/seeds and cached Stable Audio 3 weights. local.py generate --job ID --offline --force explicitly replaces a selected source and retains previous generation metadata. prepare.py --job ID [ID ...] masters selected jobs while preserving all other production bytes and ledger entries. Exported the twelve repaired masters to their pilot/weapon folders; refreshed both provenance manifests.
- All twelve music tracks and original-six/common effects remain byte-identical. New fixed-fixture envelope checks reject all twelve old noisy sources and accept the repaired sources. Their final-fifth/peak-fifth RMS ratios fall from .850–1.000 to .008–.037. This checks these one-shot fixtures, not arbitrary future noise-based effects or subjective sound design. See [verification memory](../../tests/AGENTS.md) for fresh runtime/distribution evidence.


## Original-mechanics expansion (2026-10-26)
Six new original transparent imagegen atlases supply four animation frames each for pilot, enemy, weapon and terrain: 96 frames across 24 component-local sheets. Source atlases are 1254-square; export_frontier.py measures fractional cell boundaries and packs each lossless crop into equal 314px padded frames. It explicitly handles only these six IDs, preserving older exports. All six source atlases and final gameplay scenes were inspected.

The older quadrant exporter skips authoring.animation_grid=[4,4]. A regression fixture proves it leaves row-atlas art and ledger entries untouched; rerunning the classic exporter must not reinterpret the new animation rows.

Eighteen new local Stable Audio 3 jobs supply six 32-second source tracks and twelve effects. Generation used cached weights offline, whole-second conditioning, and the existing trimming/fades/loop mastering pipeline. Sources, prepared audio and 42 local exports have recorded hashes. manifest.py verifies 260 sources/derivatives; decode/silence and one-shot envelope checks pass. Physical speaker listening is separate from these audio checks. The game never imports the authoring tools.

## Glasswake loop repair (2026-10-26)
The generated 32s source has a faded/silent outro in seconds 30–32. Source bytes/provenance remain unchanged. The prompts job now declares loop_region=[0,30]; prepare.music_loop validates/crops this explicit region before the existing 0.18s cyclic crossfade. The new 29.82s master and Pak copy have refreshed hashes and an explicit processing record. Only Glasswake music was remastered; other masters and all source files remain unchanged. Tests check region validation and non-silent 100ms windows across the shipped two-second repeat boundary. This is deterministic mastering, not a new generation or a physical listening claim.

## Initial-twelve renewal asset stage (2026-10-26)
Twelve fresh built-in imagegen sources are saved as assets/images/<pak>-renewal-source.png; exact prompts and measured actual geometry are registered only after delivery. renewal-prompts.json is the authoring plan, not evidence of generation. export_renewal.py measures low-alpha row boundaries, uses a shared significant-alpha registration crop across each four-frame row, and copies without resampling into equal padded frames. Sky enemy art uses 1.75 padding so its feet match the flat-foot collision radius under the generic renderer. Source originals remain unchanged.

The exporter writes 48 animation sheets, twelve separate decorative background textures and 36 local audio copies (96 outputs). Source sprites are no longer the original-six shared-atlas poses; backgrounds no longer copy the same title screen. Both legacy exporters skip animated sources. Changed PNGs stage outside watched Pak directories and replace atomically with brief permission retries; identical audio/PNG bytes avoid reopening streamed/previewed files. This resolved transient Windows write failures without stopping another process.

Twelve original-six attack/special effects were generated with cached local Stable Audio 3 weights, whole-second inference, and separately mastered into distinct local copies. Eleven older music loops now select explicit measured source regions before cyclic crossfade; healthy Sky Forge music is byte-identical. output/renewal-music-processing.json records before/after seam ratios; sources were not regenerated or modified for loop repairs. The stage manifest verifies 296 sources/derivatives and three media tests pass. Physical listening remains separate. Gameplay and distribution verification completed; see docs/verification.json under initial_twelve_renewal for exact evidence and limitations.

Renewal final media check: tools/verify_renewal_media.py scans the encoded cyclic join in 100ms windows every 10ms. Iron Circuit needed a further 100ms trim from its earlier selected ending; prompts.json now declares [0,31], source WAV unchanged, and the encoded minimum join/peak RMS ratio is 0.6346. All twelve exceed .075 in this scan. The current media snapshot is output/renewal-media.json; output/renewal-music-processing.json remains the earlier aligned-window mastering stage. Assets/audio/prepared.json and the main provenance manifest carry current processing/hashes.

## Pickup chime (2026-10-26)
A new pickup job (seed 2641) was generated offline using cached Stable Audio 3 SFX weights: one-second source, mastered to a 0.45s rising glass-bell reward chime. Source/model/seed/hash and mastering metadata are recorded normally. export_pickups.py copies that same mastered original into every independently copyable weapon folder (18 copies); this is one generation, not eighteen distinct generations. Manifest now verifies 316 entries.

## Facing and playtest asset refinement (2026-10-26)
Built-in imagegen delivered sixteen selected pilot sources and one four-pose sword source. Ten pilots use 8×4, five 4×4, and Sky 2×4; no unused Star/Orbit directions or discarded eight-way Sky draft are delivered. export_facings.py snapshots the exact old pilot inputs, registers prompts, measures significant-alpha subject bounds and centers lossless cell crops at one fixed pixel scale; Sky feet align to the frame bottom. Frame grids and per-role source overrides live in Pak authoring metadata. Both row exporters preserve these overrides. Seventeen selected originals, sixteen input snapshots, two original offline Stable Audio 3 sword effects and derivatives have recorded hashes. Neon retains its source but selects [0,20.8] before the fade; encoded full-join energy is checked. See the refinement verification snapshot for current counts and limits.

## Arcade feedback (2026-10-26)

Three pilot targets restore their original single-pose atlas crops with their original source/operation/hash records: Orbit Keeper, Void Drifter and Iron Circuit. No new image generation was required. Facing sources and their reference snapshots remain historical authoring evidence. authoring.pilot_rendering=rotated_single plus [1,1] role metadata prevents export_facings.py and the renewal row exporter from overwriting the chosen restoration. The active remaining directional grids are fourteen sheets/344 frames.

## Quiet presentation and tail routing (2026-10-28)

export_facings.py accepts measured source_row_edges and --pak for a targeted existing job. Maze Muncher uses [0,316,603,895,1246] in its unchanged 1262x1246 original; uniform source quarters had cut the final pose and included the next pose in the preceding row. Only its pilot derivative and corresponding provenance metadata were re-exported. All sixteen significant-alpha subject masks match their measured source crops. Do not return this source to uniform quarter cuts.

## Shared arcade defeat sound (2026-10-28)
game_over is a new actual local Stable Audio 3 small-sfx generation, seed 2846, one-second inference, offline CPU/XNNPACK/w8a8 at pinned revision 77e0398c26f7d22d801ec1bb036307e8b231f741. local.py generate --job game_over --offline completed; the prompt and original WAV hash are in prompts.json and audio/local/generation.json. prepare.py --job game_over trimmed onset, faded, normalized and encoded a .554s OGG; manifest.py registers source and derivative (356 current asset records). Runtime only loads the production sound through the effects bus. Windows and wheel include it explicitly; no generation dependency is added to the game.
