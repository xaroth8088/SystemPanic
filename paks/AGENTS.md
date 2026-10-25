# External Pak memory

Read [the root wiki](../AGENTS.md), [authoring guide](../docs/paks.md), [public ABCs](../src/system_panic/pak_api.py) and [runtime architecture](../docs/architecture.md).

## API 4 contract
- Each Pak contains role folders: pilot, enemy, weapon, music, background, obstacles. Code and its assets live together. Entry files match the role, except obstacles uses obstacle.py.
- The corresponding ABCs are PilotBase, EnemyBase, WeaponBase, MusicBase, BackgroundBase and ObstaclesBase. Concrete classes implement their explicit abstract methods. Use init() and load_asset() for local handles; private attribute names are never discovered or prescribed by the engine.
- A complete Pak supplies all six types and can play solo/coherently. A partial Pak supplies any nonempty subset and joins only its eligible pools. Complementary partials can collectively cover all six without a complete Pak.
- Music and background selection are independent of pilot and obstacle selection. Rendering/track methods must not mutate simulation or gameplay RNG. Obstacles build(world) creates fresh engine-owned Cover geometry every level/provider change; [] is valid.
- Catalogs contain immutable class/factory definitions. Every world owns fresh component instances. Replacing a component discards its private state and stops owned sound voices; locked instances survive unrelated swaps.
- Component-local image handles support spritesheet frames. Sound handles follow effects volume, support idempotent loops and stop on suspend/replacement/end. Music is streamed separately through MusicBase.track().
- Asset-only variants inherit a component class and map local filename overrides in that component's manifest configuration. Override asset filenames rather than depending on private attribute names. Providers must be installed; missing/cyclic dependencies are isolated.
- Local helper imports stay in component namespaces and reload from fresh source. A module with multiple matching subclasses must export COMPONENT or configure its class name.
- Keep spawn/relocation bounded and complete Paks independently playable. Mixed movement/weapon combinations may be awkward or ineffective until the next swap; do not force universal reach or destructible cover. Use engine state/helpers; do not advance projectiles twice or copy opaque state between components.
- Keep original AI provenance. export_paks.py records 48 local derivatives/copies across the launch set. No model/generation dependencies enter the runtime.
- new_pak.py copies a runnable complete or partial starter without overwriting. Record durable decisions in this page, each Pak's memory and the nearby component memories.

API 1 flat modules and API 2 trait-driven rules were superseded. API 4 actor factories own stats and local state; weapons receive every raw input step and own cadence. Enemy take_damage/on_contact/on_death hooks own armor, attacks, rewards and children. ProjectileBase/EffectBase helpers in each Pak own their full update/draw behavior. The core only schedules these objects, removes inactive/dead objects, preserves shared body state and supplies neutral geometry/damage services.

The core owns shared run flow: endless +1 initial-enemy progression, defeat/clear state, the initial introduction, the one-second cleared message and quarter-second periodic glitch. Paks own spawn_position, aiming, difficulty mapping, protection/healing/rewards and pilot defeat effects through explicit lifecycle callbacks. Do not reintroduce named weapon/enemy/ability features or default combat behavior into that host layer.

ObstaclesBase.take_damage(world, obstacle, damage) owns durability. Its additive API 4 default preserves raw damage; override with zero for permanent geometry. Every attacker, including drilling and enemy attacks, calls world.hit_cover instead of writing Cover.health. Maze Muncher and Vector Coil choose impervious geometry; Star Bastion retains destructible bunkers.

API 4 adds build(world), EnemyBase.spawn_position(world), ComponentBase.on_level_start/on_level_complete/on_shuffle and PilotBase.on_death. Hooks default to no action. Each launch enemy folder owns its difficulty/tactics helpers; each launch obstacle generator uses a private RNG seeded by run seed and level. Geometry regenerates on every level even in solo/locked play; music/background swaps preserve damage. Keep these policies in components rather than introducing new host traits.

Twelve complete Paks are now supplied. The expansion's six role trees have independent original sprite/audio files and local helpers; none import another Pak or a host behavior registry. Optional aim_direction/status pilot queries extend API 4 without requiring older pilots to implement them. Weapons respect deliberate pilot direction before assistance. A buffered/grid pilot must allow an escape turn when mixed cover is off-grid; a persistent weapon must forget projectiles cleared by level/swap transitions.


Collectibles are weapon-local helpers, not a seventh mix channel: copy weapon/powerup.py along with the weapon folder. Implement WeaponBase.create_powerup(world, position) and a PowerupBase subclass with update/draw; call world.collect_powerup(self) on the Pak's pickup condition. Use world.powerups_collected in weapon formulas, keep preview/init world-free, and capture local asset handles/color in the drop so it survives provider changes. The engine owns only the tenth-kill cadence and shared collection count. Shipped drops expire after 50 active seconds.

Custom Cover subclasses can override overlaps_circle/overlaps_segment, blocks_body/blocks_projectile, on_contact, damage and draw. Use world.geometry for collision queries; bounding rects are broad-phase metadata. Racetrack rails block bodies and pass shots; nonblocking black holes supply active attraction; Vector owns temporary regions/lines. Register those with world.set_geometry(self, shapes) and clear them on deactivation; locked weapon geometry survives unrelated swaps. Do not borrow another component's private state or put these mechanics in core.
