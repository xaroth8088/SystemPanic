# Sky Forge: pilot

Read [this Pak's memory](../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py). `pilot.py` subclasses `PilotBase`. Required: `create(world, position), update(world, dt, control), sprite(world, entity=None)`. Own body stats, raw input edges, ability timers, locomotion and take_damage/on_contact behavior. Jump/orbit/dash state stays here, never in core models.

Load local handles in `init()`; their attribute names are private choices. Instances belong to one run. Use explicit lifecycle callbacks for setup/cleanup. Rendering cannot advance gameplay. The host schedules projectile/effect callbacks once; do not also advance them from the component update. Local helper modules and assets can be copied as partial components. Preserve asset provenance.

on_level_start owns the 15-point between-level heal and 2-second protection; on_shuffle owns 1.5-second protection; on_death owns its burst. demo_controls includes the no-enemies intermission case. No host combat policy supplies these defaults.

The pilot uses radius 22 to match its 44px sprite; movement passes that same radius to the neutral substepped resolver. Landing/head contacts zero vertical velocity; only a landing restores jumps. Do not solve clipping by drawing the sprite inside solid geometry.

Rectangular deck landings use a flat foot span of one body diameter: while descending across a plain Cover's top, stop at top minus radius even when overhanging an edge. This prevents the circular corner contact from pinning the pilot below the walkable top. Resolve horizontal motion first so only the actual reachable position supplies support; blocked movement toward a nearby deck must not suspend gravity. Side/head collisions still use the neutral circle resolver. Apply this rule only to exact Cover objects; custom shapes' rects are broad-phase bounds, not implied solid decks. Regression and rendered evidence live in [verification memory](../../../tests/AGENTS.md).

Renewal QA uses ordinary digital input. When targets are below a support, it walks off the nearest edge and keeps that direction until fully clear vertically; it does not jump back onto the lip. These private demo flags do not affect live controls or grant movement. Enemy physics and sword rules live in their own independently copied roles.

Facing refinement: the local pilot sheet is 2 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Sky has right/left running poses plus a jump pose, with the feet aligned to the 44px frame bottom. Original built-in imagegen source: assets/images/sky_forge-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection. Pilot QA emits only eight digital directions and ordinary held/released buttons; live movement keeps the same Controls contract.

## Arcade feedback (2026-10-26)

The bottom movement boundary is now HEIGHT=480, while side/top margins remain 10px. The 22px body feet and the bottom-aligned 44px pilot poses rest on the same physical floor as platforms. Flat deck landing, edge walking and double jumping retain their existing collision protocol.
