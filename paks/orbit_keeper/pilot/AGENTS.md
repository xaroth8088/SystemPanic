# Orbit Keeper: pilot

Read [this Pak's memory](../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py). `pilot.py` subclasses `PilotBase`. Required: `create(world, position), update(world, dt, control), sprite(world, entity=None)`. Own body stats, raw input edges, ability timers, locomotion and take_damage/on_contact behavior. Jump/orbit/dash state stays here, never in core models.

Load local handles in `init()`; their attribute names are private choices. Instances belong to one run. Use explicit lifecycle callbacks for setup/cleanup. Rendering cannot advance gameplay. The host schedules projectile/effect callbacks once; do not also advance them from the component update. Local helper modules and assets can be copied as partial components. Preserve asset provenance.

on_level_start owns the 15-point between-level heal and 2-second protection; on_shuffle owns 1.5-second protection; on_death owns its burst. demo_controls includes the no-enemies intermission case. No host combat policy supplies these defaults.

Radial movement uses 70/115/160/205-pixel rings, one discrete step per accepted up/down press or sign change; held vertical input does not continuously change radius. Own _fire_outward here. Flip it only when the special press is accepted, not on every held step. aim_direction/status are read-only queries; the flag persists between levels/locked swaps. Angular movement state remains separate from the actual radial firing vector after collision displacement. The QA policy keeps a target and predicts collision risk; it must not alter enemy health or bypass input.

Renewal: local four-frame horizontal animation and read-only frame selection. Pilot QA emits only eight digital directions and ordinary held/released buttons; live movement keeps the same Controls contract.

## Arcade feedback (2026-10-26)

The pilot now uses the original single-pose crop from assets/images/sprites-source.png, restored byte-for-byte with its original provenance. sprite returns the raw ImageAsset; sprite_angle rotates it by -degrees(body.angle)-90. Movement, abilities, acceleration, gravity and weapon formulas were retained. authoring.component_grids.pilot=[1,1] and pilot_rendering=rotated_single preserve this choice through later asset exports.
