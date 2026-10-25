# Iron Circuit: enemy

Read [this Pak's memory](../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py). `enemy.py` subclasses `EnemyBase`. Required: `spawn_position(world), create(world, identity, position), advance_enemy(world, enemy, dt), sprite(world, entity=None)`. Own spawn stats/local entity state, AI clocks, take_damage, on_contact and on_death. Rewards and child factories belong here; the host infers no family or splitting trait.

Load local handles in `init()`; their attribute names are private choices. Instances belong to one run. Use explicit lifecycle callbacks for setup/cleanup. Rendering cannot advance gameplay. The host schedules projectile/effect callbacks once; do not also advance them from the component update. Local helper modules and assets can be copied as partial components. Preserve asset provenance.

Turrets fire faster/harder shots, lead moving targets after level 3 and alternate three-shot fans from level 8. Circuit generators vary paired banks and the central island. Local tactics.py interprets difficulty and owns spawn clearance/probing. on_level_complete awards 250 * level; contact and bullet damage grow with level. Movement/fire curves approach readable limits; health and damage keep growing.
