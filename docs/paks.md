# Building a Pak: component folders and ABCs

Paks are external folders. Their layout is the first guide to the API: each component keeps its Python class and assets together. The six shipped games are complete, working examples of API 4.

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
    projectile.py
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
| pilot | PilotBase | create(world, position), update(world, dt, control), sprite(world, entity=None) |
| enemy | EnemyBase | spawn_position(world), create(world, identity, position), advance_enemy(world, enemy, dt), sprite(world, entity=None) |
| weapon | WeaponBase | update(world, dt, control), sprite(world, entity=None) |
| music | MusicBase | track(world=None) |
| background | BackgroundBase | draw(surface, world) |
| obstacles | ObstaclesBase | build(world), sprite(world, entity=None) |

Override init(self) to load local asset handles and initialize private state. The engine owns construction. Use activate(world) for setup that needs engine-owned state, deactivate(world) for replacement/end-of-run cleanup, and suspend() for optional pause behavior (call super().suspend() to retain sound cleanup). PilotBase also offers demo_controls(world) for an optional ordinary-input QA policy. preview() provides an optional library thumbnail.

A pilot whose folder contains pilot_sheet.png, idle.ogg and moving.ogg can be written like this:

```python
from system_panic.pak_api import PilotBase
from system_panic.model import Pilot, Vec


class MyPilot(PilotBase):
    controls = "Arrows / WASD: move"
    special = "Hold X: boost"

    def init(self):
        self.spritesheet = self.load_asset("pilot_sheet.png")
        self.idle_sounds = self.load_asset("idle.ogg")
        self.moving_sounds = self.load_asset("moving.ogg")

    def sprite(self, world, entity=None):
        return self.spritesheet

    def create(self, world, position):
        return Pilot(pos=Vec(position), health=100, max_health=100, radius=11)

    def update(self, world, dt, control):
        direction = Vec(control.x, control.y)
        if direction.length_squared() > 1:
            direction.normalize_ip()
        world.player.vel = direction * (400 if control.special else 220)
        world.move_body(world.player, world.player.vel * dt, world.player.radius)
        if direction.length_squared():
            self.idle_sounds.stop()
            self.moving_sounds.play(loop=True, volume=0.3)
        else:
            self.moving_sounds.stop()
            self.idle_sounds.play(loop=True, volume=0.2)
```

spritesheet, idle_sounds and moving_sounds are ordinary author-owned attributes. The engine never looks for them. It calls the explicit API methods, such as sprite(), to obtain the handle you choose. Use any attribute names you prefer.

load_asset() resolves inside that component's folder. PNG/WebP/JPEG files yield ImageAsset handles; OGG/WAV files yield SoundAsset handles. Loading is lazy and does not open a display or audio device. Missing files and paths escaping the component folder are rejected. Assets from an inherited component can be overridden by filename without depending on the provider's private Python attributes.

For a grid spritesheet, return self.spritesheet.frame(index, columns=4, rows=2) from sprite(). Frame selection is row-major; dimensions must divide evenly. Use world.time for a simulation-based animation clock. sprite_angle(world, entity) and sprite_flip_x(world, entity) provide generic presentation transforms. Projectile drawing and orientation belong to the Pak, too.

SoundAsset.play(loop=True) keeps a single loop active until stop(). Playback follows the effects preference. Engine-owned cleanup stops a component's voices on pause/focus loss, replacement, intermissions, defeat and run end. Sound is silent in simulation-only worlds without an audio service. MusicBase.track() returns a sound handle (or None for silence); the engine streams it using the music preference.

## What belongs to each component

PilotBase.create() chooses the body's stats and update() receives raw held Controls on every active step. The Pak decides input edges, movement, abilities, hit handling and recovery timing. WeaponBase.update() likewise owns all triggering, cadence, charge and burst logic. There is no host cooldown property or automatic firing gate.

Controls are device-independent. Keyboard, left stick and D-pad provide x/y in [-1, 1] (negative y is up); stick travel is quantized after per-axis deadzones to the exact same eight digital directions as the D-pad; magnitude does not scale speed or steering. Fire/special remain held booleans. Keep device polling, menu buttons and mappings in the shell; a Pak should act on Controls and implement its own input edges. Existing API 4 Paks need no changes for gamepads. controls/special descriptions may still describe their keyboard actions; the shell supplies the controller binding guide and hints.

EnemyBase.spawn_position(world) chooses initial placement, including any distance from the player. EnemyBase.create() receives the host's unique identity and a suggested position, and returns an Enemy body with Pak-owned stats/state. The Pak advances its own AI clocks. Override take_damage(), on_contact() and on_death() for armor, contact attacks, rewards, transformations and child spawns. These hooks have neutral/no-op defaults: the host does not classify families or infer splitting. The shipped Void Drifter's on_death() creates its two fragment bodies itself.

The core Body/Pilot/Enemy data has only common physical/health state. A Pak can subclass Enemy for its own per-entity fields, as the shipped Paks do. Host swaps preserve identity, position and shared health while the new Pak's factory creates clean local state. Obstacle constructors provide their own health/max_health; build(world) returns fresh Cover objects and [] is valid.

BackgroundBase.draw() owns scenery without collision geometry. MusicBase owns the independently selected track. Both are separate shuffle channels, alongside pilot, enemy, weapon and obstacles. Drawing, sprite selection and track selection must not advance gameplay or consume gameplay RNG. See the shipped background and music classes for complete examples.

Import state and geometry helpers from system_panic.model: Body, Pilot, Enemy, Controls, Cover, Vec, WIDTH, HEIGHT, unit, normalized and circle_rect. world.move_body() resolves geometry and returns Motion collision normals. It does not change velocity, reset jumps, wrap the screen or decide bounce behavior. Paks make those decisions; bounds=None permits unconstrained motion before a Pak applies its own wrapping.

world.apply_damage(body, amount) is a neutral health/protection primitive. world.hit_player() and hit_enemy() dispatch to the selected Pak's take_damage() policy. Spawn extra enemies with world.spawn_enemy(position, factory=your_factory); the factory has the same (world, identity, position) signature as EnemyBase.create(). The host registers identities and calls on_death() once after removing dead bodies. The Pak chooses any rewards/child counts.

world.component("pilot") and other literal component names provide typed IDE return values. world.pak(channel) supplies display metadata. The host owns shared run state, fixed-step scheduling, user preferences, the required endless +1 initial-enemy progression and established transition/level-clear flow. Paks own spawn/swap protection, level healing/bonuses, aiming and difficulty interpretation. The host has no factor or aim policy; safe_position accepts optional away_from/clearance geometry constraints chosen by the caller.

### Projectiles and visual effects

Implement ProjectileBase in a local helper such as weapon/projectile.py or enemy/bullet.py. Its constructor provides position, velocity, radius and alive; update(world, dt) owns every motion, lifetime and collision outcome. draw(graphics, surface, world) owns presentation. Append instances to world.projectiles. The host invokes update() once per active step and removes objects marked alive=False; it does not add another motion step, expire shots or infer their team.

The six Paks implement piercing, ricochet, homing, area damage and returning flight in their own projectile classes. There is no host feature-flag constructor for these behaviors. Call the neutral geometry/hit services or apply Pak-specific rules directly. is_threat_to(world, body) is an optional query for Pak demo AI and has no host gameplay interpretation.

Visual-only transients can implement EffectBase.update(dt) and draw(graphics, surface, world) and join world.effects. The host schedules them, including during intermissions. Gameplay effects must instead run in active component/projectile updates. Phase Garden owns its lightning visual in weapon/arc.py. Graphics.render_sprite() is a reusable image/frame sizing primitive; it does not infer the shot's behavior.

Every run receives fresh component instances. Instances stay alive while their component remains selected; a replacement receives clean private state. Different worlds never share private counters or sound handles. Background/music swaps preserve locked pilot/enemy instances and obstacle state. Every new level replaces obstacle geometry even when its provider is locked or playing solo.

## Manifest and class discovery

```json
{
  "api_version": 4,
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
  "api_version": 4,
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

API 1 flat modules, API 2 trait-driven components and API 3 are superseded by API 4. API 3 authors must add EnemyBase.spawn_position(world), change ObstaclesBase.build() to build(world), and move any reliance on world.factor/world.aim into their components. Use the optional lifecycle hooks below for protection/rewards. Move firing gates into WeaponBase.update(), actor stats into create(), enemy death behavior into on_death(), and flight/hit logic into Pak projectile classes. Pilot input/ability clocks and per-enemy state are local too. Folder conventions and asset handles are retained. All eighteen supplied Paks are migrated examples. Old arena/pilot shuffle preferences migrate to the corresponding new channels on load.

Complete Paks must be independently playable, but awkward or ineffective component mixes are allowed until the next shuffle. Cover may be impervious. Check complete Paks solo and partial Paks in eligible mixes. The compatibility runner checks stability in all pilot/enemy/weapon/obstacle combinations plus all background/music presentation pairs; it reports these separately. --require-clear is an optional balance probe, not a requirement for all mixes. Pak code is trusted local Python, with the normal permissions of the game process. The game does not fetch Paks or install arbitrary dependencies.

## Levels, procedural layouts and difficulty

All components optionally receive on_level_start(world), on_level_complete(world) and on_shuffle(world, changed). changed is a frozenset of replaced channel names; unchanged components receive it too. These callbacks default to no action. PilotBase.on_death(world) optionally supplies defeat effects. No automatic healing, protection or score bonus is applied by the host.

At level arrival, the host increments world.wave, clears old projectiles, calls obstacles.build(world), repairs the pilot's geometric overlap, invokes all on_level_start callbacks, then creates exactly world.wave initial enemies using spawn_position/create. The new layout replaces all damaged/destroyed cover; locked components retain their instances and private state. A changed obstacle provider also builds for the current level during a periodic shuffle. Unrelated presentation swaps preserve the existing cover.

When enemies are gone, on_level_complete callbacks run once before the one-second clear screen. Shipped pilots choose per-level recovery and arrival/swap protection; the selected enemy component awards the level bonus. These are editable Pak choices. The host still owns endless +1 initial enemy counts and transition timing.

Use world.wave (the current one-based level), world.seed, world.prefs.difficulty and world.player state directly in local rules. Spawn factories and active updates see the current level; cached stats must be refreshed deliberately when needed. Shipped enemies increase health/contact damage and differentiate their tactics: interception/flanking swarms, hunting asteroid fragments, predictive/fan turrets, faster ricocheting crawler dashes, closer/predictive phantom teleports and pursuing sentinel formations. Movement and firing approach readable limits; count, health and damage continue growing.

Obstacle generation should use a private seeded RNG rather than consume world.rng (which drives combat). Here is a complete asset-free obstacle component:

```python
import random
from pygame import Rect
from system_panic.model import Cover
from system_panic.pak_api import ObstaclesBase


class MyObstacles(ObstaclesBase):
    def sprite(self, world, entity=None):
        return None

    def build(self, world):
        rng = random.Random(f"{world.seed}:my_obstacles:{world.wave}")
        return [Cover(Rect(rng.randint(180, 300), 140, 40, 100), 36, 36)]
```

Return new objects on each build. Keep generation bounded, leave broad passages and margins, and ensure no draw/preview method advances RNG. Copy local helper modules along with their component folder when authoring partial Paks. Run python tools/verify_levels.py to check the launch layouts across seeds/levels and render a comparison gallery.

## Optional firing intent and state hints

PilotBase.aim_direction(world) defaults to None. A pilot may instead return its deliberate firing vector, such as Orbit Keeper's inward/outward mode. Weapons should query it before their ordinary aim-assist/facing selection; guided projectiles should preserve deliberate direction instead of silently reacquiring a different target. This is an additive API 4 query, not a host aiming policy. PilotBase.status(world) defaults to an empty string and can describe live state in the keyboard/gamepad footer. Neither query may mutate simulation or RNG.

The six expansion folders provide additional authoring examples: a persistent multiball pool in neon_breach/weapon, buffered turns with off-grid obstacle escape in maze_muncher/pilot, drilling and inflation in burrow_patrol, closed-tail intersections, containment and scheduled capture visuals in vector_coil, formation and dive behavior in star_bastion, and timed hops/catch-and-reel flight in tide_hopper. Persistent component references to scheduled objects must account for the host clearing projectiles at level/swap transitions; prune references that are no longer registered before launching again.

Obstacle durability uses ObstaclesBase.take_damage(world, obstacle, damage). The default applies raw damage for API 4 compatibility; returning zero makes cover impervious. All attacks call world.hit_cover(obstacle, damage), including drilling and enemy impacts. Keep finite health for geometry/rendering rather than using infinite health.


## Collectible API (additive API 4)

Keep a weapon's PowerupBase subclass in weapon/powerup.py so the whole weapon folder remains copyable as a partial Pak. The engine calls create_powerup(world, position) at every tenth removed enemy. All shipped weapons implement the factory; the default None keeps older external weapon implementations loadable. A drop owns its image handle/color so changing Paks does not change its behavior or invalidate rendering.

PowerupBase supplies pos, vel, radius and alive, with abstract update(world, dt) and draw(graphics, surface, world). No movement, gravity, lifetime or pickup radius policy is inferred by the host. Call world.collect_powerup(self) when the Pak's pickup condition is met. The host checks live membership and prevents double collection, increments world.powerups_collected and calls the currently active weapon's on_powerup(world, count). Read that count in weapon formulas. It starts at zero per run and survives level/weapon changes; uncollected drops survive those transitions too. Updates freeze during pause/glitch/clear/ready states.

For example, inside an existing WeaponBase subclass:

```python
from .powerup import MyPowerup

def create_powerup(self, world, position):
    return MyPowerup(position, self.load_asset("weapon_sheet.png"))

def on_powerup(self, world, count):
    world.burst(world.player.pos, world.pak("weapon").color, 12)
# In the weapon's own attack logic: damage = 16 + 4 * world.powerups_collected
```

All eighteen supplied folders provide local motion and upgrade policies. The README records the current mapping. Do not add upgrade formulas or pickup movement branches to the core.

## Shape and lifetime APIs

world.cover is the selected obstacle component's list. world.geometry combines it with registered component-owned shapes. Use world.set_geometry(self, shapes) for weapon-created territory/live barriers and world.clear_geometry(self) when releasing it. The host also releases a component's registrations on replacement/close. Geometry does not have to belong to the obstacle mix channel.

Cover subclasses may override overlaps_circle(position, radius), overlaps_segment(start, end), blocks_body(body), blocks_projectile(projectile), on_contact(world, body, normal), damage(world, amount) and draw(graphics, surface, world). Their rect is a broad-phase bound, not necessarily a solid rectangle. Always query the methods instead of assuming rectangle collision. Projectiles use blocks_projectile plus overlaps_circle; rays use world.segment_blocked. A racetrack can return False from blocks_projectile while remaining solid to bodies. Component-specific responses, such as reflecting an enemy at a live tail, belong in the shape callback.

ObstaclesBase.update(world, dt) runs once per active step after actor/projectile motion; use it for gravity wells, crossing hazards and moving geometry. draw_floor(graphics, surface, world) paints terrain underneath shapes and must be simulation-free. move_body provides bounded substeps and shape-contact normals without deciding jumping/ricochet policy; safe_position accepts body= for shape filtering. Keep all lifecycle cleanup and procedural rules in the owning Pak.

A shape that fully handles its collision response may return True from on_contact; the resolver then suppresses that contact normal in Motion. This prevents caller AI from applying a second reflection. Default contacts return no handled result and preserve neutral normal reporting.

## Original-mechanics examples

The six newest Paks demonstrate release-edge resonance and public-threat parries (Pulse Abbey), inertial orbital salvage (Scrap Ballet), reflected rays with heat recovery (Glasswake), growth and cascading traps (Bloom Siege), delayed recorded volleys and safe positional rewind (Echo Vault), and buoyancy/entraining pressure bubbles (Tidal Choir). Each contains six independently copyable roles and four-frame component spritesheets.

Keep movement/special descriptions in the pilot and firing descriptions in the weapon's own readout. A pilot hint that describes its original weapon becomes misleading in a Remix. Pulse Abbey's weapon owns a gold timing cue so its visual beat remains usable with another pilot/background/obstacle set. Generated music is not a sample-accurate timing source.

Held input is not a universal damage promise: charged weapons may require release. Test full charge/release cycles, pruning of host-cleared persistent objects, per-target hit windows, cold init/preview, geometry cleanup and copied partial roles. Demonstration policies should select the same eight digital directions as keyboard/D-pad, without analog steering or speed advantages. See tools/verify_frontier.py and tools/verify_frontier_mixes.py for reproducible bounded samples.

## Optional destruction notifications and weapon QA input
ComponentBase.on_enemy_destroyed(world, enemy) receives each removed dead actor once, after the kill counter, tenth-kill powerup check and enemy on_death. Defaults to no action; replacing/adopting/despawning enemies does not emit it. Components choose any reaction locally. Scrap Ballet uses this to create physical salvage for any enemy provider, without asking the host to classify a drop.

WeaponBase.demo_controls(world, controls) may refine the pilot's ordinary QA Controls. Its default returns the supplied object unchanged. This hook applies only to autopilot, never live keyboard/gamepad input. New charge/resource weapons use digital input to collect real scrap, refill actual water and satisfy their charge thresholds. No QA policy may directly grant resources or combat advantages.

Bloom Siege demonstrates independently copied resource geometry: its weapon registers its own nonblocking nectar wells, owns capacity/current water and spends nectar on growth. The obstacle folder contains only root gates. Powerup upgrades need not improve direct damage: Bloom expands can capacity, while plant damage remains a function of nectar spent.

## Arcade feedback (2026-10-26)

Optional presentation callbacks: PilotBase.draw(graphics,surface,world,*,reduced_motion=False) and EnemyBase.draw(graphics,surface,world,enemy,*,reduced_motion=False) default to the prior centered sprite presentation. Override locally for shape/pivot alignment without changing simulation or RNG. A Pilot subclass may override Body.overlaps_circle(position,radius) to describe its contact footprint; the default remains circular. Weapons may use that public query. The nominal radius still supplies existing terrain queries unless a component explicitly chooses another local motion policy.

### Navigation collision snapshots

`navigation_key()` optionally returns a hashable immutable collision snapshot. Equal keys promise identical `overlaps_circle` results for a given radius, with `rect` conservatively bounding the shape. Include all relevant parameters; body filtering remains a separate query. The default opts in only for inherited rectangle overlap and returns `None` for custom queries. Custom segments/polygons can opt in explicitly so another component can share exact sampled navigation graphs across equal recreated shapes. Consumers still call the real overlap methods; they must not turn the bounding rectangle into solid geometry or infer gameplay features from keys.
