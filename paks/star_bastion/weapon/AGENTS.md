# Star Bastion: weapon

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). This folder owns all behavior/helpers/assets; copy the whole folder as a partial Pak. No sibling-role private state or other Pak imports. Use public world/body/shape contracts. Drawing and sprite selection cannot change simulation or RNG.

Battery 4+min(4,floor(n/2)) cells. Salvos cost one cell every .32s; empty reload 1.35s. Release with cells remaining for .48s to refill early. Damage 23+4n, 2+min(4,floor(n/3)) bolts. Assistance/guidance stays in a narrow .94-dot forward cone. Bolts expire at screen edges, never wrap.

The local sheet has four horizontal animation frames. Pickups capture the raw local ImageAsset and select their own frame when drawn, so provider changes cannot break them. The engine owns tenth-kill scheduling and the persistent collected count; powerup.py owns movement/pickup/expiry and this weapon interprets the count.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).

## Quiet presentation and tail routing (2026-10-28)

Fixed top-left heat, speed, charge, energy, battery, nectar and cooldown readouts are removed. This role retains its attacks and existing on-pilot physical/charge/resource feedback where applicable. Empty readout scheduling/helpers were removed when they served no other presentation. Weapon mechanics are unchanged; this supersedes earlier fixed-HUD meter notes.
