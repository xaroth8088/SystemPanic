# System Panic

An offline arcade game about adapting as its rules change around you. Play any of twenty-four complete Paks alone, mix their components, or build a static Remix by choosing its pilot, enemies, weapon, music, background and obstacles. Survive an endless sequence of levels: start with one enemy, then face two, three, and one more with every cleared level. The run ends when you are defeated.

This is a fresh implementation. The 2017 game and unfinished 2025 rewrite remain available in Git history; see [prototype history and credits](docs/history.md).

## Play on Windows

Double-click **`run.bat`**. It uses Python 3.12, creates a project-local virtual environment and installs Pygame 2.6.1, the only runtime dependency. After that first setup, playing requires no network connection.

If a standalone build is present, run **`dist/SystemPanic/SystemPanic.exe`**. Keep the entire `SystemPanic` folder together; no Python installation is needed for that build.

```sh
python -m pip install -r requirements.txt
python play.py
```

Source also runs on Linux/macOS with Python 3.12+ and Pygame; the standalone build targets Windows x64.

## The twenty-four Paks

| Pak | Movement | Weapon | Opposition |
|---|---|---|---|
| Signal Runner | Eight-way strafing and invulnerable dash | Burst pulse fire; release to vent heat | Flanking leeches with locked lunges and safe recovery |
| Void Drifter | Rotation, inertial thrust and reverse braking | Charge and release piercing lances with recoil | Asteroids that fracture into smaller rocks |
| Iron Circuit | Automatic acceleration, steering and overdrive ramming | Momentum strengthens plasma; banks add power | Turrets lock their aim and expose armor after shots |
| Sky Forge | Gravity, double jumping and rising forge leap | Sweep overhead with knockback, or charge a sword throw and retrieve it | Crawlers leap between decks and leave active rooftop heat |
| Phase Garden | Rhythmic step-dashes and blinking through cover | Finite lightning links; upgrades add reach and arcs | Flowers mark their warp destinations, then expose themselves |
| Orbit Keeper | Orbit and step between rings; special toggles inward/outward fire | Bounded returning glaives; timed release catches empower the next blade | Circling sentinels with firing and armor windows |
| Neon Breach | Perimeter paddle sliding and magnetic corner bursts | Paddle returns build plasma power; missed returns drain it | Brick drones lock their aim before firing |
| Maze Muncher | Buffered cardinal turns and energized contact chomps | Contact lunges; backbites hit harder and stun | Chase/scatter crabs in a new maze each level, with randomized wrap exits |
| Burrow Patrol | Cardinal digging and a close-range drill burst | Maintain pressure within tether reach, then recover after a pop | Worms burrow, then immediately rush a locked target |
| Vector Coil | Continuous right-angle movement and shielded reversals | Close tails around whole enemies; solid territory gradually fades | Hard-hitting sparks pause, then dart in random directions |
| Star Bastion | Horizontal movement along the bottom and barrel rolls | Align narrow salvos; release early to reload the battery faster | Armored formations fire spread volleys near you and expose themselves during dives |
| Tide Hopper | Discrete lane hops and long ferry leaps | Catch traffic, hold to reel, or release to fling it into an impact | Wrapping traffic hops and pauses on the pilot’s 48px grid |
| Pulse Abbey | Bell dancing and a protected step | Compact rings expand with upgrades; gold releases deal 8x offbeat damage | Cantors lock their lunge direction, then expose themselves during recovery |
| Scrap Ballet | Inertial thrust, magnetic braking and repulsion | Collect drifting scrap, then hurl it; wrecks replenish the field | Rival tugs intercept, orbit and commit to ramming runs |
| Glasswake | Gliding prism skates and a quarter-turn dash | Heat-limited ray gains 3× damage per reflection | Shielded skaters strafe and fire ricocheting predictive fans |
| Bloom Siege | Botanical scuttling and protected burrow hops | Refill at pools that move each level; leave the pool to plant and water | Weevils stalk, lock their target and rush through your garden |
| Echo Vault | Movement with a two-second positional rewind | Record volleys that repeat from their original locations and directions | Chronoguards predict movement, leave active danger zones and blink to flanks |
| Tidal Choir | Buoyant swimming, ballast dives and pressure shielding | Charge at least 0.6s; bubbles rebound with energy loss before their timed burst | Cuttlefish space themselves, lock jet charges and leave active ink hazards |
| Canopy Capers | Primary button jumps; gravity, double jumps and a leaf glide | Automatic descending stomps scale with relative impact speed and build rebound chains | Lantern beetles plan physical routes up/down spring branches and collapsing leaves |
| Rime Rink | Inertial skating with a deliberate carve brake | Throw finite curling stones, then skate over them to recover ammunition | Ice crabs skid through warm braking strips and moving crushers |
| Storm Loom | Drifting kite flight with an anchor stance | Throw and reel a harpoon; release to snap its taut, damaging thread | Shoot turbines to rotate solid gates and powerful jet lanes; wall impacts hurt both sides |
| Kiln Derby | Ceramic racing with a draft dash | Pressure strengthens molten marbles; release cools the nozzle before it locks | Furnaces rotate between slag volleys; shooting hot slag creates protective ceramic cover |
| Paper Pilgrimage | Glide and commit to a folded dart | Fold paper around the pilot while charging, then release a blade that cuts, unfolds and returns | Paper mantises dart through paired fold gates and shot-open moving shutters |
| Ferric Ferry | Magnetic tug momentum and a reversing repel pulse | Plant two terminals, energize their fixed induction rail, then release a sweeping armature | Rivet skiffs bank through reversible magnetic fields and projectile-transparent rails |

The classic-inspired six use original designs based on familiar arcade mechanics: **Neon Breach → Breakout**, **Maze Muncher → Pac-Man**, **Burrow Patrol → Dig Dug**, **Vector Coil → Qix / Tron**, **Star Bastion → Space Invaders**, and **Tide Hopper → Frogger**. They retain System Panic's endless combat objective and mixable components. Each owns its code, procedural layouts, original AI sprites, soundtrack and effects.

Each Pak has its own procedural arena geometry, original generated sprites and soundtrack. Obstacles regenerate every level, and enemies gain speed, damage and more advanced tactics as levels rise. Signal partitions, Sky Forge platforms, Phase Garden hedges, maze walls and capacitor posts are impervious. Iron Circuit uses closed racetrack rails that stop bodies and pass projectiles; Void Drifter includes gravitational wells and timed crossing comets. Other obstacle Paks choose their own durability. Awkward or ineffective component combinations are allowed to persist until the next shuffle. Shared engine state survives a shuffle; opaque movement/AI state does not.

## Collectible powerups

Every **ten enemies destroyed**, the engine asks the active weapon Pak to create a collectible at that enemy's position. Each weapon folder contains its own `powerup.py` subclass of `PowerupBase`. Paks own movement, lifetime, pickup conditions and presentation. Pickup counts persist across levels and Pak swaps; the active weapon interprets the total. The HUD's **UP** value shows collected upgrades. Uncollected drops keep their original behavior when weapons change.

| Pak | Collectible behavior | Weapon upgrade |
|---|---|---|
| Signal Runner | Magnetic drift nearby | Damage and faster firing |
| Void Drifter | Inertial drift and wrapping | Lance damage, speed and piercing |
| Iron Circuit | Rolling, bouncing cell | Damage, pellet count and ricochets |
| Sky Forge | Falls and lands on platforms | Sweep/throw damage and sweep reach |
| Phase Garden | Periodic blink toward the pilot | Damage; another arc every three pickups, capped at five targets |
| Orbit Keeper | Orbits its drifting pickup center | Glaive damage, outbound reach and blade pool |
| Neon Breach | Bouncing bonus ball | Ball damage and multiball capacity |
| Maze Muncher | Stationary power pellet | Dash damage, reach and recovery |
| Burrow Patrol | Digs toward the pilot in steps | Tether reach (145 to 300 px), pressure and damage |
| Vector Coil | Follows cardinal grid directions | Longer/wider tail and charged contact damage |
| Star Bastion | Falling supply cell | Salvo damage, additional bolts and battery capacity |
| Tide Hopper | Drifts across the river lane | Harpoon damage and reel speed |
| Pulse Abbey | Nearby magnetic collection | Resonance damage and range |
| Scrap Ballet | Nearby magnetic collection | Salvage damage, collection reach and carrying capacity |
| Glasswake | Nearby magnetic collection | Ray damage and reflection count |
| Bloom Siege | Nearby magnetic collection | Watering can capacity (+2 nectar per pickup, up to 24) |
| Echo Vault | Nearby magnetic collection | Echo damage and repeat count |
| Tidal Choir | Nearby magnetic collection | Powered burst size and damage; minimum charge stays 0.6s |
| Canopy Capers | Nearby attraction | Stronger stomps and higher rebounds |
| Rime Rink | Nearby attraction | Stone damage, faster throws and up to two extra recoverable stones |
| Storm Loom | Nearby attraction | Harpoon, reel and snap damage |
| Kiln Derby | Nearby attraction | Marble damage and rebound count |
| Paper Pilgrimage | Nearby attraction | Blade damage and unfolding reach |
| Ferric Ferry | Nearby attraction | Stronger/wider armatures and longer charge capacity (1.2 to 2.4 seconds) |

Vector's filled regions and live enemy-blocking lines are owned by its weapon component. Filled regions retain a walkable boundary, survive unrelated swaps for their remaining lifetime, and fade after 22 active seconds. Weapon replacement or a new level clears them. The pilot's attacks remain device-independent.

## Dynamic Paks

The eighteen Paks are ordinary external folders under [`paks/`](paks/AGENTS.md), separate from the game engine. Each contains `pak.json` and six component folders with code and local assets. Classes subclass the discoverable ABCs in `system_panic.pak_api`; handles such as `self.spritesheet` are private author choices. Add a Pak folder and choose **Rescan Paks** in the library; no registry change or executable rebuild is needed. Use **Pak status** for installation locations and skipped-Pak errors. The library supports more than six Paks with pagination.

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
- **Space:** current weapon input. Several Paks use charging, release timing, venting, reloading or resource collection; the arena explains the active weapon. Aim assistance follows the weapon's own targeting limits and can be disabled.
- **X / Shift:** current pilot's special, with a short cooldown.
- **Escape:** pause or back. Losing window focus also pauses gameplay.
- **F11:** fullscreen.
- **Mouse, or Tab / arrows + Enter:** menus. Enter from the library starts the selected mix.

SDL-mapped gamepads work in gameplay and every menu, with hot-plug detection. The stick selects the same eight digital directions as the D-pad: any accepted deflection has the same movement speed and steering; there is no analog movement. Open **Preferences → Gamepad / Input** for the connected controller, stick deadzone and button guide. Xbox / PlayStation button positions:

| Control | Action |
|---|---|
| Left stick or D-pad | Pilot movement; directional menu focus |
| RT / R2 or A / Cross | Fire; A / Cross selects in menus |
| X / Square or LB / L1 | Pilot special |
| Start / Options | Pause / resume |
| B / Circle | Back in menus |
| LB / RB in menus | Previous / next page |

An active controller disconnect pauses the run. After connecting, resuming or changing screens, release the stick/buttons before the next action; held menu confirmation cannot fire or select again. Periodic Pak glitches and level changes resume held gameplay input automatically. Keyboard/mouse remain available, and hints follow the last input used. Compatible devices use the [SDL mapping exposed by Pygame](https://www.pygame.org/docs/ref/sdl2_controller.html); arbitrary unmapped joysticks need an SDL mapping. Custom button remapping is not included.

The library's **Start Main Game** uses the **Enabled** Paks as its shuffle pool. **Play Solo** starts a complete Pak with every component locked to it. Partial Paks show **Mix Only** and contribute only their declared components. The enabled mix must cover pilot, enemy, weapon, music, background and obstacles. The main game selects each component independently from its eligible enabled providers.

Choose **Remix / Build & Play** to select one installed Pak for each of the six components and play with those providers fixed for the entire run. Remix can use Paks outside the main game's enabled pool, including partial Paks for the components they supply. Levels still add enemies and regenerate terrain normally. Some combinations may be awkward or ineffective.

Use **Save As New** and **Saved Remixes** to keep favorite combinations; open a favorite to play, rename or delete it. Keyboard users can type names; mouse and gamepad users can use the on-screen keys. During a run, pause and choose **Save Current Mix** to capture the active six Pak choices without leaving the paused run. A favorite starts a fresh game at level one; it does not restore score, health, upgrades, terrain or progress. Saved Remix cards list all six providers, including unavailable selections, with four cards per page. Favorites save locally in `remixes.json` beside `preferences.json`. If a required Pak is removed, the favorite stays available for renaming, deletion or component replacement, and cannot start until all six choices are available.

Periodic randomization pauses for a quarter-second screen glitch, then resumes automatically. Clearing a level instead shows a one-second **Level Cleared** message before the next level starts, without another readiness screen. The initial ready introduction appears only when starting a new run.

If active gameplay stays below **10 FPS for more than one second**, the engine pauses and lists all six active components. That exact combination is saved in `blocked_combinations.json` beside preferences and excluded from future starts and shuffles. In the main game, **Reshuffle & Continue** keeps run progress and selects another combination allowed by the enabled Paks and component locks; **Main Menu** is also available. Static Remix, solo play, or a run with no remaining alternative returns to the menu. Pauses, focus loss, level messages and provider transitions do not count toward detection.

Open **Preferences → Flagged Combinations** to inspect the components, detection time and measured FPS, or **Re-enable This Combination** to try it again. A blocked favorite remains editable; replace a component or re-enable it before playing. If saving fails, the combination stays disabled for the current session and the dialog offers a disk-save retry.

Preferences include coherent/component shuffle, 5–30 second intervals, component locks, three difficulty levels, audio levels, aim assistance, reduced motion and fullscreen. Music and effects buttons adjust by **5 percentage points**. **Preferences → Display** selects windowed/fullscreen output and a saved rendering resolution, from 960 × 600 through 3840 × 2160. Automatic keeps a 1280 × 800 window or the desktop resolution in fullscreen. Scaling preserves the aspect ratio and field of view; it does not change the gamefield or simulation resolution. Progression is always endless; older finite-run settings are ignored. Gameplay changes apply to the next run; audio/display changes apply immediately. Preferences and best score save to `%LOCALAPPDATA%/SystemPanic/preferences.json` on Windows, or the platform's user data directory elsewhere.

```sh
python play.py --solo void_drifter --seed 24
python play.py --data-dir ./my-local-profile
python play.py --headless --demo --frames 480 --solo sky_forge --seed 24 --screenshot output/sky.png
```

## Development and agent memory

Start at [`AGENTS.md`](AGENTS.md). Linked wiki pages live beside the runtime, Paks, tests and asset tools. See [`docs/architecture.md`](docs/architecture.md) for engine architecture, [`docs/paks.md`](docs/paks.md) for the Pak format and callback interface, and [`docs/history.md`](docs/history.md) for the removed prototypes.

```sh
python -m unittest discover -s tests -v
python tools/verify.py
python tools/verify_combinations.py
python tools/compatibility.py
python tools/verify_platforms.py
python tools/verify_powerups.py --frozen
python tools/verify_renewal.py
python tools/verify_renewal_mixes.py
```

`verify.py` samples each endless solo run through twelve cleared levels, verifies the one-enemy-per-level increase, and checks play continues on level thirteen. It writes screenshots plus a report; `--levels` changes this QA stopping point without changing the game. `compatibility.py` checks stable gameplay updates in every eligible pilot/enemy/weapon/obstacle mixture (**104,976** with the eighteen shipped Paks) and separately renders/streams all **324** background/music pairs using a fixed seed and relaxed difficulty. `--require-clear` optionally probes opening-level balance; some mixes are deliberately ineffective until a shuffle and need not clear. Automated gameplay checks complement human balance testing.

## Original AI asset pipeline

Generation is separate from the game. The runtime only reads local finished assets and never contacts a model service.

- Sprite atlas and title illustration: built-in **OpenAI imagegen**. Full prompts and inspected atlas geometry: [`tools/assetforge/image-prompts.json`](tools/assetforge/image-prompts.json).
- Eighteen soundtracks and Pak-local effects: **Stable Audio 3**, generated locally using the [official Windows LiteRT backend](https://github.com/Stability-AI/stable-audio-3/tree/main/optimized/tflite). Initial cloud generations are retained as source history; the game ships mastered local outputs.
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

The input UI supports keyboard, mouse and SDL-mapped gamepads. Custom remapping and an online catalog remain outside this version's scope.

## Credits

Concept: Geoffrey Benson. Inspiration: *ROM CHECK FAIL* by Farbs. Revival code uses the repository's MIT license. Generated asset provenance is recorded in the manifest. Historical asset credits are preserved in [prototype history](docs/history.md).
