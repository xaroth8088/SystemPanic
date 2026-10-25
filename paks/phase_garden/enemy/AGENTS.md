# Phase Garden: enemy

Read [this Pak's memory](../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py). `enemy.py` subclasses `EnemyBase`. Required: `spawn_position(world), create(world, identity, position), advance_enemy(world, enemy, dt), sprite(world, entity=None)`. Own spawn stats/local entity state, AI clocks, take_damage, on_contact and on_death. Rewards and child factories belong here; the host infers no family or splitting trait.

Load local handles in `init()`; their attribute names are private choices. Instances belong to one run. Use explicit lifecycle callbacks for setup/cleanup. Rendering cannot advance gameplay. The host schedules projectile/effect callbacks once; do not also advance them from the component update. Local helper modules and assets can be copied as partial components. Preserve asset provenance.

Phantoms move faster, teleport closer/more often and target the predicted pilot path. Shots re-aim after relocation. Hedge generators vary disconnected maze partitions and gaps. Local tactics.py interprets difficulty and owns spawn clearance/probing. on_level_complete awards 250 * level; contact and bullet damage grow with level. Movement/fire curves approach readable limits; health and damage keep growing.
