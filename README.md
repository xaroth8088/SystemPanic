# System Panic

**Twelve worlds. One unstable system.**

An offline arcade game about adapting as its rules change around you. Play any of twelve complete Paks alone, shuffle whole Paks together, or independently remix their pilots, enemies, weapons, music, backgrounds and obstacles. Survive an endless sequence of levels: start with one enemy, then face two, three, and one more with every cleared level. The run ends when you are defeated.

This is a fresh implementation. The 2017 game and unfinished 2025 rewrite are preserved under [`legacy/`](legacy/AGENTS.md); the revival does not import their code or assets.

## Play on Windows

Double-click **`run.bat`**. It uses Python 3.12, creates a project-local virtual environment and installs Pygame 2.6.1, the only runtime dependency. After that first setup, playing requires no network connection.

If a standalone build is present, run **`dist/SystemPanic/SystemPanic.exe`**. Keep the entire `SystemPanic` folder together; no Python installation is needed for that build.

```sh
python -m pip install -r requirements.txt
python play.py
```

Source also runs on Linux/macOS with Python 3.12+ and Pygame; the standalone build targets Windows x64.

## The twelve Paks

| Pak | Movement | Weapon | Opposition |
|---|---|---|---|
| Signal Runner | Eight-way strafing and invulnerable dash | Rapid pulse fire | Chasing insect swarm |
| Void Drifter | Rotation, inertial thrust and reverse braking | Piercing lance | Asteroids that fracture into smaller rocks |
| Iron Circuit | Constant driving, steering and overdrive ramming | Ricocheting scattershot | Aimed gun turrets |
| Sky Forge | Gravity, double jumping and rising forge leap | Seeking explosive fireballs | Hopping forge crawlers |
| Phase Garden | Rhythmic step-dashes and blinking through cover | Four-target chain lightning | Teleporting spectral flowers |
| Orbit Keeper | Angular/radial movement; special reverses, shields and toggles inward/outward fire | Radially directed returning glaives | Circling sentinels |
| Neon Breach | Perimeter paddle sliding and magnetic corner bursts | Accelerating, bouncing multiball | Moving brick drones |
| Maze Muncher | Buffered cardinal turns and energized contact chomps | Expanding directional chomp waves | Chase/scatter maze crabs |
| Burrow Patrol | Cardinal digging and a close-range drill burst | Pressure tether that inflates and pops targets | Armored burrowing worms |
| Vector Coil | Continuous right-angle movement leaving damaging trails | Sweeping four-arm prism laser | Reflecting vector sparks |
| Star Bastion | Lower-sky banking and barrel rolls | Twin wrapping, guided salvo bolts | Sweeping formations with later diving attacks |
| Tide Hopper | Discrete lane hops and long ferry leaps | Catch-and-reel harpoons | Wrapping traffic with later lane interception |

The additional six use original designs inspired by classic mechanics: **Neon Breach → Breakout**, **Maze Muncher → Pac-Man**, **Burrow Patrol → Dig Dug**, **Vector Coil → Qix / Tron**, **Star Bastion → Space Invaders**, and **Tide Hopper → Frogger**. They retain System Panic's endless combat objective and mixable components. Each owns its code, procedural layouts, original AI sprites, soundtrack and effects.

Each Pak has its own procedural arena geometry, original generated sprites and soundtrack. Obstacles regenerate every level, and enemies gain speed, damage and more advanced tactics as levels rise. All cover can be destroyed and every weapon can reach each enemy family. Shared engine state survives a shuffle; opaque movement/AI state does not.

## Dynamic Paks

The twelve Paks are ordinary external folders under [`paks/`](paks/AGENTS.md), separate from the game engine. Each contains `pak.json` and six component folders with code and local assets. Classes subclass the discoverable ABCs in `system_panic.pak_api`; handles such as `self.spritesheet` are private author choices. Add a Pak folder and choose **Rescan Paks** in the library; no registry change or executable rebuild is needed. Use **Pak status** for installation locations and skipped-Pak errors. The library supports more than six Paks with pagination.

The Windows build loads `paks/` beside its executable and `%LOCALAPPDATA%/SystemPanic/paks`. A source checkout uses project-root `paks/` plus the same user location. Complete Paks can run alone; partial Paks can supply any subset of the six component types. Asset-only partial Paks can inherit installed behavior and add their own sprites. Complementary partial Paks can form a playable mix without a complete Pak.

See [installation, manifest examples and callback API](docs/paks.md).

```sh
python play.py --list-paks
python play.py --pak-dir ./my-paks
python tools/new_pak.py paks/my_pak
python tools/new_pak.py paks/my_weapon --components weapon
```

## Controls and preferences

- **Arrows / WASD:** current pilot's movement; the live footer shows the active controls.
- **Space:** hold to fire. Aim assistance targets the nearest enemy by default and can be disabled.
- **X / Shift:** current pilot's special, with a short cooldown.
- **Escape:** pause or back. Losing window focus also pauses gameplay.
- **F11:** fullscreen.
- **Mouse, or Tab / arrows + Enter:** menus. Enter from the library starts the selected mix.

SDL-mapped gamepads work in gameplay and every menu, with hot-plug detection. Open **Preferences → Gamepad / Input** for the connected controller, stick deadzone and button guide. Xbox / PlayStation button positions:

| Control | Action |
|---|---|
| Left stick or D-pad | Pilot movement; directional menu focus |
| RT / R2 or A / Cross | Fire; A / Cross selects in menus |
| X / Square or LB / L1 | Pilot special |
| Start / Options | Pause / resume |
| B / Circle | Back in menus |
| LB / RB in menus | Previous / next page |

An active controller disconnect pauses the run. After connecting, resuming or changing screens, release the stick/buttons before the next action; held menu confirmation cannot fire or select again. Periodic Pak glitches and level changes resume held gameplay input automatically. Keyboard/mouse remain available, and hints follow the last input used. Compatible devices use the [SDL mapping exposed by Pygame](https://www.pygame.org/docs/ref/sdl2_controller.html); arbitrary unmapped joysticks need an SDL mapping. Custom button remapping is not included.

The library's **Enabled** buttons control the remix pool. **Play Solo** starts a complete Pak with every component locked to it. Partial Paks show **Mix Only** and contribute only their declared components. The enabled mix must cover pilot, enemy, weapon, music, background and obstacles. Coherent shuffle selects complete Paks; component remix also includes partial Paks.

Periodic randomization pauses for a quarter-second screen glitch, then resumes automatically. Clearing a level instead shows a one-second **Level Cleared** message before the next level starts, without another readiness screen. The initial ready introduction appears only when starting a new run.

Preferences include coherent/component shuffle, 5–30 second intervals, component locks, three difficulty levels, audio levels, aim assistance, reduced motion and fullscreen. Progression is always endless; older finite-run settings are ignored. Gameplay changes apply to the next run; audio/display changes apply immediately. Preferences and best score save to `%LOCALAPPDATA%/SystemPanic/preferences.json` on Windows, or the platform's user data directory elsewhere.

```sh
python play.py --solo void_drifter --seed 24
python play.py --data-dir ./my-local-profile
python play.py --headless --demo --frames 480 --solo sky_forge --seed 24 --screenshot output/sky.png
```

## Development and agent memory

Start at [`AGENTS.md`](AGENTS.md). Linked wiki pages live beside the runtime, Paks, tests, asset tools and historical code. See [`docs/architecture.md`](docs/architecture.md) for engine architecture and [`docs/paks.md`](docs/paks.md) for the Pak format and callback interface.

```sh
python -m unittest discover -s tests -v
python tools/verify.py
python tools/compatibility.py
```

`verify.py` samples each endless solo run through twelve cleared levels, verifies the one-enemy-per-level increase, and checks play continues on level thirteen. It writes screenshots plus a report; `--levels` changes this QA stopping point without changing the game. `compatibility.py` plays an opening level in every eligible pilot/enemy/weapon/obstacle gameplay mixture (**20,736** with the twelve shipped Paks) and separately renders/streams all **144** background/music pairs using a fixed seed and relaxed difficulty. Automated gameplay checks complement human balance testing.

## Original AI asset pipeline

Generation is separate from the game. The runtime only reads local finished assets and never contacts a model service.

- Sprite atlas and title illustration: built-in **OpenAI imagegen**. Full prompts and inspected atlas geometry: [`tools/assetforge/image-prompts.json`](tools/assetforge/image-prompts.json).
- Six music tracks and all six effects: **Stable Audio 3**, generated locally using the [official Windows LiteRT backend](https://github.com/Stability-AI/stable-audio-3/tree/main/optimized/tflite). Initial cloud generations are retained as source history; the game ships mastered local outputs.
- [`assets/manifest.json`](assets/manifest.json) records prompts, seeds, providers, hashes and production processing. Historical third-party art and music are not included in the new distribution.

The local generator has its own environment and cached model weights under ignored `.asset-tools/`, separate from the game's environment and build. After the initial downloads, music and effects generation work offline. `run_audio.bat` starts a loopback-only browser studio at **http://127.0.0.1:7871**, with no public link.

```sh
python tools/assetforge/local.py install
python tools/assetforge/local.py generate --job all --offline
python -m pip install ".[assets]"
python tools/assetforge/prepare.py
python tools/assetforge/manifest.py
```

Mastering trims/fades effects and normalizes/crossfades music into loops. Installed FFmpeg produces Vorbis files under `assets/audio/production`; without it, mastering produces PCM WAVs. Image generation uses the built-in tool, followed by copying selected outputs to `assets/images` and recording their prompt/hash.

## Build a Windows distribution

```sh
python -m pip install ".[build]"
python tools/build.py
```

The build packages only the active runtime, production assets and license. Historical prototypes, source WAVs, generation code, credentials and development environments are excluded. Assets resolve independently of the current working directory.

The current input UI uses keyboard and mouse. Gamepad support, remappable controls and an online catalog are outside this version's scope.

## Credits

Concept: Geoffrey Benson. Inspiration: *ROM CHECK FAIL* by Farbs. Revival code uses the repository's MIT license. Generated asset provenance is recorded in the manifest. Historical prototypes retain their credits in `legacy/README.md`.
