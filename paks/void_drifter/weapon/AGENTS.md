# Void Drifter: weapon

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). This folder owns all behavior/helpers/assets; copy the whole folder as a partial Pak. No sibling-role private state or other Pak imports. Use public world/body/shape contracts. Drawing and sprite selection cannot change simulation or RNG.

Hold .18-1.15s then release; .22s recovery. With normalized strength s, damage 18+58s+7n, speed 580+330s+min(160,12n), penetration 1+round(3s)+floor(n/2). Recoil 25+90s acts on the public pilot velocity. Short taps produce no lance.

The local sheet has four horizontal animation frames. Pickups capture the raw local ImageAsset and select their own frame when drawn, so provider changes cannot break them. The engine owns tenth-kill scheduling and the persistent collected count; powerup.py owns movement/pickup/expiry and this weapon interprets the count.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).

## Quiet presentation and tail routing (2026-10-28)

Fixed top-left heat, speed, charge, energy, battery, nectar and cooldown readouts are removed. This role retains its attacks and existing on-pilot physical/charge/resource feedback where applicable. Empty readout scheduling/helpers were removed when they served no other presentation. Weapon mechanics are unchanged; this supersedes earlier fixed-HUD meter notes.
