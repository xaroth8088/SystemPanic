# External Pak memory

Read [the root wiki](../AGENTS.md), [authoring guide](../docs/paks.md), [public ABCs](../src/system_panic/pak_api.py) and [runtime architecture](../docs/architecture.md).

## API 2 contract
- Each Pak contains role folders: pilot, enemy, weapon, music, background, obstacles. Code and its assets live together. Entry files match the role, except obstacles uses obstacle.py.
- The corresponding ABCs are PilotBase, EnemyBase, WeaponBase, MusicBase, BackgroundBase and ObstaclesBase. Concrete classes implement their explicit abstract methods. Use init() and load_asset() for local handles; private attribute names are never discovered or prescribed by the engine.
- A complete Pak supplies all six types and can play solo/coherently. A partial Pak supplies any nonempty subset and joins only its eligible pools. Complementary partials can collectively cover all six without a complete Pak.
- Music and background selection are independent of pilot and obstacle selection. Rendering/track methods must not mutate simulation or gameplay RNG. Obstacles build fresh engine-owned Cover geometry; [] is valid.
- Catalogs contain immutable class/factory definitions. Every world owns fresh component instances. Replacing a component discards its private state and stops owned sound voices; locked instances survive unrelated swaps.
- Component-local image handles support spritesheet frames. Sound handles follow effects volume, support idempotent loops and stop on suspend/replacement/end. Music is streamed separately through MusicBase.track().
- Asset-only variants inherit a component class and map local filename overrides in that component's manifest configuration. Override asset filenames rather than depending on private attribute names. Providers must be installed; missing/cyclic dependencies are isolated.
- Local helper imports stay in component namespaces and reload from fresh source. A module with multiple matching subclasses must export COMPONENT or configure its class name.
- Keep weapons able to reach every enemy family, cover destructible and spawn/relocation bounded. Use engine state/helpers; do not advance projectiles twice or copy opaque state between components.
- Keep original AI provenance. export_paks.py records 48 local derivatives/copies across the launch set. No model/generation dependencies enter the runtime.
- new_pak.py copies a runnable complete or partial starter without overwriting. Record durable decisions in this page, each Pak's memory and the nearby component memories.

API 1 flat modules were superseded and all launch Paks migrated. The core owns endless +1 enemy progression, the initial introduction, the one-second cleared message and quarter-second periodic glitch.
