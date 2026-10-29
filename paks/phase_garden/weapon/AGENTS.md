# Phase Garden: weapon

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). This folder owns all behavior/helpers/assets; copy the whole folder as a partial Pak. No sibling-role private state or other Pak imports. Use public world/body/shape contracts. Drawing and sprite selection cannot change simulation or RNG.

First reach 190+min(120,12n), following links 110+min(80,8n), min(5,2+floor(n/3)) targets, damage 26+3n. Explicit aim requires a forward cone. Arcs phase through cover by design; no global target reach.

The local sheet has four horizontal animation frames. Pickups capture the raw local ImageAsset and select their own frame when drawn, so provider changes cannot break them. The engine owns tenth-kill scheduling and the persistent collected count; powerup.py owns movement/pickup/expiry and this weapon interprets the count.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

Playtest refinement: no radius circle, numerical reach or range-miss label is presented. The finite reach/link formulas remain mechanical rules the player discovers through positioning and arcs.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).
