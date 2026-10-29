# External Pak memory

Read [the root wiki](../AGENTS.md), [authoring guide](../docs/paks.md), [public ABCs](../src/system_panic/pak_api.py) and [runtime architecture](../docs/architecture.md).

## API 4 contract
- Each Pak contains role folders: pilot, enemy, weapon, music, background, obstacles. Code and its assets live together. Entry files match the role, except obstacles uses obstacle.py.
- The corresponding ABCs are PilotBase, EnemyBase, WeaponBase, MusicBase, BackgroundBase and ObstaclesBase. Concrete classes implement their explicit abstract methods. Use init() and load_asset() for local handles; private attribute names are never discovered or prescribed by the engine.
- A complete Pak supplies all six types and can play solo. A partial Pak supplies any nonempty subset and joins only its eligible pools. Complementary partials can collectively cover all six without a complete Pak.
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

Twenty-four complete Paks are now supplied. The expansion's six role trees have independent original sprite/audio files and local helpers; none import another Pak or a host behavior registry. Optional aim_direction/status pilot queries extend API 4 without requiring older pilots to implement them. Weapons respect deliberate pilot direction before assistance. A buffered/grid pilot must allow an escape turn when mixed cover is off-grid; a persistent weapon must forget projectiles cleared by level/swap transitions.


Collectibles are weapon-local helpers, not a seventh mix channel: copy weapon/powerup.py along with the weapon folder. Implement WeaponBase.create_powerup(world, position) and a PowerupBase subclass with update/draw; call world.collect_powerup(self) on the Pak's pickup condition. Use world.powerups_collected in weapon formulas, keep preview/init world-free, and capture local asset handles/color in the drop so it survives provider changes. The engine owns only the tenth-kill cadence and shared collection count. Shipped drops expire after 50 active seconds.

Custom Cover subclasses can override overlaps_circle/overlaps_segment, blocks_body/blocks_projectile, on_contact, damage and draw. Use world.geometry for collision queries; bounding rects are broad-phase metadata. Racetrack rails block bodies and pass shots; nonblocking black holes supply active attraction; Vector owns temporary regions/lines. Register those with world.set_geometry(self, shapes) and clear them on deactivation; locked weapon geometry survives unrelated swaps. Do not borrow another component's private state or put these mechanics in core.


## Original-mechanics expansion (2026-10-26)
Pulse Abbey, Scrap Ballet, Glasswake, Bloom Siege, Echo Vault and Tidal Choir each supply six independent API 4 roles. They do not import other Paks or sibling roles. Mechanics use public body, geometry, scheduling and lifecycle contracts. The resource refinement adds generic optional destruction notifications and weapon demo-input refinement; the host interprets no Pak-specific resources or rules. Four-frame animation rows are extracted from six original AI atlases by tools/assetforge/export_frontier.py; each role keeps its own sheet/audio.

Charged weapons depend on release edges. A held trigger alone is not a universal damage contract. Scrap/Tidal/Bloom prune references to projectiles cleared by the host before rebuilding persistent attacks. Readout projectiles provide weapon-local charge/heat hints, including with a foreign pilot. Rewind restores only a safe past position and protection, never health, score, kills or projectiles. Rhythm judgement uses the visible 0.6-second simulation beat, not a promise of sample-accurate generated music synchronization. See each Pak's memory and the newest verification snapshot for measured limits.

## Resource and charge refinement (2026-10-26)
ComponentBase.on_enemy_destroyed(world, enemy) is an optional once-only notification after kill counting and enemy on_death; adoption/despawning never emits it. Scrap uses it for physical debris drops regardless of enemy provider. WeaponBase.demo_controls(world, controls) optionally refines the pilot QA policy; the default returns its input and live player controls never pass through this method. These neutral services do not move drop/resource/charge/aim rules into the engine.

Bloom wells belong to its weapon and use owned nonblocking geometry, allowing independent partial installation with foreign obstacles. Do not restore obstacle-owned healing/nectar rules or automatic growth. See the five Pak memories and newest verification snapshot for exact charge, inventory, loop and capacity behavior.

## Initial-twelve renewal (2026-10-26)
The first twelve own four-frame local pilot/enemy/weapon/terrain rows and animated pickups. Retain raw ImageAsset handles in collectibles, then select frames in their draw method. SpriteFrame is a view, not a file handle. Asset-only overrides must match the inherited animation grid. Both legacy exporters preserve animated sources. See [the renewal ledger](../docs/pak-renewal.json) for tested evidence and per-Pak outcomes.

Their mechanics now include burst venting, charge/recoil, momentum banks, cooked grenades, finite lightning links, timed blade catches, powered paddle returns, backbites, pressure recovery, expiring territory, salvo batteries and traffic flings. Helpers, state, rules, geometry and readouts remain inside the owning role. No sibling-private-state dependencies were added. All twelve were also checked as isolated complete installs and as six complementary partial folders.

QA routes use ordinary digital controls. Buffered grid pilots must reject a snap into actual geometry and must not commit to a moving target's unreachable off-grid coordinate. Committed waypoint traversal avoids repeated nearest-node reversal. These are local authoring decisions, not new engine behavior. Vector territory lasts 22 active seconds to avoid permanent empty-region dead ends; the baseline live line still only bounces.

## Pickup chimes (2026-10-26)
Each shipped weapon owns pickup.ogg and captures its SoundAsset in the created powerup. A successful collect_powerup return gates playback in the Pak, so only actual collection chimes once. Do not attach the sound to the newly active weapon: surviving older drops retain their originating audio. Effects volume/mute and unavailable-device behavior use the existing neutral SoundAsset bus; no new host rule or API is needed.

## Playtest refinement (2026-10-26)
Sixteen pilots now own movement-specific facing grids: ten use eight bearings, five cardinal pilots use four, Sky uses two upright run/jump facings. Star retains its forward ship and Orbit its symmetric spin. component_grids/component_sources in authoring metadata document assets; the host never interprets them as gameplay. Legacy and row exporters preserve overrides. The sword, wrap maze, boundary network, grid traffic, chipped bunkers and softer gravity stay in their owning roles; see [the refinement ledger](../docs/playtest-refinement.json).

## Arcade feedback (2026-10-26)

All in-arena control prose and redundant facing ticks/dots are removed at their owning draw sites; numerical resources and mechanical meters remain. Footer/menu control help is separate. Default pilot/enemy drawing now has optional read-only draw hooks; the host only dispatches them. Body.overlaps_circle defaults to a circle and permits a Pak subclass contact footprint. Neon uses these general primitives for its wider flat paddle; Sky aligns crawler feet; Tide omits the movement circle. No named Pak rule enters the host. See [latest feedback evidence](../docs/arcade-feedback.json).

## Moving-mirror navigation performance (2026-10-26)

The BUGGY fixed mix (Sky pilot/background, Maze enemies, Tidal weapon, Glass obstacles, Echo music) is a regression for moving-collider pathfinding. Maze enemy navigation shares only verified rectangle-overlap topology, includes effective body filters, and keeps arbitrary shapes conservative. Its immutable probe template carries no run state; snapshot history is bounded. No Pak-specific logic or cache was added to the host. See [the enemy memory](maze_muncher/enemy/AGENTS.md).

## Quiet presentation and live-tail navigation (2026-10-28)
Advance attack lines, target markers, windup/recovery rings and inactive danger-zone previews are removed. Phase Garden retains only its creature teleport destination circle. Attack delays/state machines and active damage presentation remain; no global telegraph trait or rendering filter is added to the host. Fixed top-left weapon meters (including Maze cooldown and Bloom nectar) are removed at their owning roles; actual attacks and on-pilot feedback remain.

Cover.navigation_key is an optional neutral collision snapshot contract. A non-None hashable key promises equal circle-overlap results for a given radius and conservative rect bounds; custom shapes include every relevant shape parameter. Body filters remain separate and must be evaluated each query. The default supports inherited rectangle overlap only. Unknown custom methods remain conservative. Vector segments/polygons opt in so Maze navigation can index exact samples and share graphs across equal recreated geometry without reading another role's private state. See the two role memories and docs/visual-cleanup.json for current evidence.

## Living Arcade expansion (2026-10-28)

Six more complete API 4 Paks bring the set to twenty-four. Canopy Capers owns gravity jumping, swept descending stomps and elastic/collapsing branches. Rime Rink owns skating, heavy curling stones, warm grip strips and moving presses. Storm Loom owns kite drift, physical reeled threads, shot-turned solid gates and hazardous jet lanes. Kiln Derby owns pressure/heat marbles and furnaces ejecting hot slag that cools into cover. Paper Pilgrimage owns folding flight, unfolding return blades, paired transport gates and shot-open shutters. Ferric Ferry owns tug momentum, planted induction rails and shot-reversed magnetic pylons/body-only rails. Every role remains independently copyable; no named rule or API addition entered the host.

The playtest revision supersedes the initial Canopy controls and damage gate: primary-button edges jump, and the weapon automatically evaluates real descending foot crossings with damage proportional to relative downward speed. Side contact, ascent and large actor teleport discontinuities do not count. Foreign pilots receive no added mobility. Beetles use their own bounded surface graph and sampled, committed ballistic routes through public shape queries; floor pursuit does not imply abandoning all platforms. Flat feet accept inherited rectangular overlap only. Rime places presses at their seeded phase before spawn placement. Storm's hook dispatches hit_cover and snap rechecks occlusion.

Storm terrain now rotates actual solid wings and drives narrow, strong jet lanes with collision-impact damage. Kiln terrain now ejects physical rolling hot slag that shots cool into solid destructible cover. Ferric's orbiting-mote weapon is replaced by two planted terminals, a fixed energized induction rail and a travelling released armature. Current and armature clipping use the actual contact radius; tiny/grazing cover must not leak damage. These mechanics remain role-local; see the nearby memories.

All twelve new actor roles now select real directional source poses with zero runtime sprite rotation/mirroring: Canopy has two facings/four animation rows, and the ten free-moving actors have eight/four. Component grids/sources and archived prior rows live in authoring metadata, which the host never treats as gameplay. The original row exporter preserves these overrides and the new rail artwork.

The six use original built-in imagegen atlases and eighteen offline local Stable Audio 3 jobs. Source prompts, measured lossless extraction and local copies live in the existing asset ledgers. Pickup chimes reuse the documented shared original. See [asset memory](../tools/assetforge/AGENTS.md) and [verification memory](../tests/AGENTS.md) for final evidence and limits.

The next refinement makes Rime ammunition physical: thrown curling stones remain on the rink and return to stock only through pilot contact, with no timed refill. Kiln furnaces turn during the rest between three-shot volleys, then hold the new emission heading. Their collision bases remain fixed so turning cannot sweep geometry into actors. Paper's weapon owns a read-only paper-folding charge animation around the active pilot; it works with foreign pilots and disappears on release. See the owning role memories and [refinement evidence](../docs/living-refinements.json). These add no host gameplay policy or new generated media.
