# Building a Pak: component folders and ABCs

Paks are external folders. Their layout is the first guide to the API: each component keeps its Python class and assets together. The six shipped games are complete, working examples of API 2.

## Start with something runnable

From a checkout:

```sh
python tools/new_pak.py paks/my_pak
python tools/new_pak.py paks/my_weapon --components weapon
python play.py --list-paks
```

The starter command copies selected component folders and their original AI assets from Signal Runner. Use --from-pak PATH to choose another example. It never overwrites an existing directory. Edit the copied classes/assets and choose **Rescan Paks** in the library. There is no registry to edit or executable to rebuild.

```text
my_pak/
  pak.json
  AGENTS.md
  pilot/
    pilot.py
    pilot_sheet.png
    special.ogg
  enemy/
    enemy.py
    enemy_sheet.png
  weapon/
    weapon.py
    weapon_sheet.png
    shot.ogg
  music/
    music.py
    music.ogg
  background/
    background.py
    background_image.png
  obstacles/
    obstacle.py
    obstacles_sheet.png
```

These are the actual shipped folder/file names. Asset filenames are chosen by the class author; a pilot can also have idle.ogg, moving.ogg or other files. Only the component folder and Python entry filename follow a convention. Each component folder has nearby agent memory describing its contract.

## The public API

Import base classes from system_panic.pak_api. Their abstract methods have docstrings and type hints, so IDEs can show the required methods and signatures.

| Folder | Base class | Required methods |
|---|---|---|
| pilot | PilotBase | move(world, dt, control, jump, special), sprite(world, entity=None) |
| enemy | EnemyBase | advance_enemy(world, enemy, dt), sprite(world, entity=None) |
| weapon | WeaponBase | fire(world, direction), sprite(world, entity=None) |
| music | MusicBase | track(world=None) |
| background | BackgroundBase | draw(surface, world) |
| obstacles | ObstaclesBase | build(), sprite(world, entity=None) |

Override init(self) to load local asset handles and initialize private state. The engine owns construction. Use activate(world) for setup that needs engine-owned state, deactivate(world) for replacement/end-of-run cleanup, and suspend() for optional pause behavior (call super().suspend() to retain sound cleanup). PilotBase also offers demo_controls(world) for an optional ordinary-input QA policy. preview() provides an optional library thumbnail.

A pilot whose folder contains pilot_sheet.png, idle.ogg and moving.ogg can be written like this:

```python
from system_panic.pak_api import PilotBase
from system_panic.model import Vec


class MyPilot(PilotBase):
    controls = "Arrows / WASD: move"
    special = "X: dash"

    def init(self):
        self.spritesheet = self.load_asset("pilot_sheet.png")
        self.idle_sounds = self.load_asset("idle.ogg")
        self.moving_sounds = self.load_asset("moving.ogg")

    def sprite(self, world, entity=None):
        return self.spritesheet

    def move(self, world, dt, control, jump, special):
        direction = Vec(control.x, control.y)
        if direction.length_squared() > 1:
            direction.normalize_ip()
        world.player.vel = direction * (400 if special else 220)
        world.move_body(world.player, world.player.vel * dt, 12)
        if direction.length_squared():
            self.idle_sounds.stop()
            self.moving_sounds.play(loop=True, volume=0.3)
        else:
            self.moving_sounds.stop()
            self.idle_sounds.play(loop=True, volume=0.2)
```

spritesheet, idle_sounds and moving_sounds are ordinary author-owned attributes. The engine never looks for them. It calls the explicit API methods, such as sprite(), to obtain the handle you choose. Use any attribute names you prefer.

load_asset() resolves inside that component's folder. PNG/WebP/JPEG files yield ImageAsset handles; OGG/WAV files yield SoundAsset handles. Loading is lazy and does not open a display or audio device. Missing files and paths escaping the component folder are rejected. Assets from an inherited component can be overridden by filename without depending on the provider's private Python attributes.

For a grid spritesheet, return self.spritesheet.frame(index, columns=4, rows=2) from sprite(). Frame selection is row-major; dimensions must divide evenly. Use world.time for a simulation-based animation clock. sprite_angle(world, entity) and sprite_flip_x(world, entity) provide generic presentation transforms. WeaponBase points sprites along projectile velocity by default.

SoundAsset.play(loop=True) keeps a single loop active until stop(). Playback follows the effects preference. Engine-owned cleanup stops a component's voices on pause/focus loss, replacement, intermissions, defeat and run end. Sound is silent in simulation-only worlds without an audio service. MusicBase.track() returns a sound handle (or None for silence); the engine streams it using the music preference.

## What belongs to each component

PilotBase.controls and special describe controls; move() updates world.player through common collision helpers. EnemyBase.family identifies the enemy state and splits specifies optional fragments; the engine advances enemy age and timer before advance_enemy(). WeaponBase.cooldown is positive seconds; fire() uses spawn_shot, damage_enemy and/or beams. ObstaclesBase.build() returns a fresh list of Cover objects each time; [] is valid for an open field.

BackgroundBase.draw() owns scenery without collision geometry. MusicBase owns the independently selected track. Both are separate shuffle channels, alongside pilot, enemy, weapon and obstacles. Drawing, sprite selection and track selection must not advance gameplay or consume gameplay RNG. See the shipped background and music classes for complete examples.

Import state and helpers from system_panic.model: Vec, Controls, Cover, Beam, WIDTH, HEIGHT, unit, normalized and circle_rect. The world owns damage, collision, projectiles, shared state, endless level progression and transition timing. world.component("pilot") and the other literal component names have typed return values for IDE discovery. world.pak(channel) returns the selected Pak's display metadata.

Every run receives fresh component instances. Instances stay alive while their component remains selected; a replacement receives clean private state. Different worlds never share private counters or sound handles. Background/music swaps preserve locked pilot/enemy instances and obstacle state.

## Manifest and class discovery

```json
{
  "api_version": 2,
  "id": "my_pak",
  "version": "1.0.0",
  "name": "My Pak",
  "subtitle": "MY ARCADE RULES",
  "description": "A complete game or a useful contribution to the mix.",
  "color": [80, 220, 255],
  "components": ["pilot", "enemy", "weapon", "music", "background", "obstacles"]
}
```

The loader imports pilot/pilot.py, enemy/enemy.py, weapon/weapon.py, music/music.py, background/background.py and obstacles/obstacle.py. Define one subclass of the appropriate base in each module. If there are multiple subclasses, export COMPONENT = MyPilot (or the corresponding class), or use a component configuration such as {"pilot": {"class": "MyPilot"}}. Relative helpers such as from .animation import choose_frame stay isolated from other Paks and are re-read on rescan.

components can be a list, a mapping of component configurations, or omitted to discover the known folders automatically. Metadata is separate from component implementations: no callback names, asset attribute names, atlas columns or behavior labels need registration in the core.

## Partial and asset-only Paks

A complete Pak supplies all six component types and can play alone or join coherent shuffle. A partial Pak supplies any nonempty subset and appears as **MIX ONLY**. Component remix uses only eligible enabled providers. Six complementary partial Paks can form a playable game without a complete Pak. The enabled pool must cover all six types; UI and preference recovery preserve that coverage. Coherent mode uses complete Paks.

For a weapon artwork variant, create only weapon/weapon_sheet.png plus a manifest like this:

```json
{
  "api_version": 2,
  "id": "alternate_pulse",
  "version": "1.0.0",
  "name": "Alternate Pulse",
  "subtitle": "WEAPON ART",
  "description": "New artwork with the existing pulse behavior.",
  "color": [255, 160, 100],
  "components": {
    "weapon": {
      "inherits": "signal_runner",
      "assets": {"weapon_sheet.png": "weapon_sheet.png"}
    }
  }
}
```

No weapon.py is needed for that variant. Its provider must be installed but need not be enabled. Inheritance reuses the class with a fresh instance; local asset overrides are applied to its load_asset() calls. Unoverridden assets remain with the provider. This also works for music-only or background-only asset variants. Missing providers and dependency cycles appear in Pak status.

## Install, verify and migrate

The Windows build discovers paks/ beside SystemPanic.exe and %LOCALAPPDATA%/SystemPanic/paks. A checkout uses project-root paks/ and the same user location; a Python installation uses share/system-panic/paks. On other platforms the user location is under $XDG_DATA_HOME/SystemPanic/paks (default ~/.local/share/SystemPanic/paks). **Pak status** lists actual locations and errors. Rescan from the library after editing files; active runs retain their catalog snapshot.

Use --pak-dir PATH (repeatable) to replace default roots, --list-paks to inspect discovery, and --solo ID to launch a complete Pak. These switches also work on the Windows executable. Source verification tools accept --pak-dir as well.

API 1's flat pak.py format has been replaced by API 2. Move its functions into the corresponding ABCs, put music in its own component, and split the old arena into background drawing and obstacle geometry. All six supplied Paks are migrated examples. Old arena/pilot shuffle preferences migrate to the corresponding new channels on load.

Keep weapons able to reach all enemy families and cover destructible. Check complete Paks solo and partial Paks in eligible mixes. The compatibility runner tests all pilot/enemy/weapon/obstacle gameplay combinations plus all background/music presentation pairs; it reports these separately. Pak code is trusted local Python, with the normal permissions of the game process. The game does not fetch Paks or install arbitrary dependencies.
