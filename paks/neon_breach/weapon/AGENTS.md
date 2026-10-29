# Neon Breach: weapon

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). This folder owns all behavior/helpers/assets; copy the whole folder as a partial Pak. No sibling-role private state or other Pak imports. Use public world/body/shape contracts. Drawing and sprite selection cannot change simulation or RNG.

Pool 2+min(3,floor(n/2)); no continuous homing. Energy starts 1.2, loses .35 per missed border and expires below .25. Paddle contact adds .65 up to 2.4, speed +65 capped 760, and adjusts angle with impact offset/tangential paddle velocity. Damage (20+6n)*energy; finite lifetime/hit clocks.

The local sheet has four horizontal animation frames. Pickups capture the raw local ImageAsset and select their own frame when drawn, so provider changes cannot break them. The engine owns tenth-kill scheduling and the persistent collected count; powerup.py owns movement/pickup/expiry and this weapon interprets the count.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

## Arcade feedback (2026-10-26)

PlasmaBall tests the public pilot overlap query with its radius+5, giving the 84px paddle useful outer-span returns. Near-border reflection normals are perpendicular to the screen edge; foreign pilots farther inside retain radial returns. Tangential offset/velocity still angle returns. Instruction prose is removed; energy bars remain.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).

## Quiet presentation and tail routing (2026-10-28)

Fixed top-left heat, speed, charge, energy, battery, nectar and cooldown readouts are removed. This role retains its attacks and existing on-pilot physical/charge/resource feedback where applicable. Empty readout scheduling/helpers were removed when they served no other presentation. Weapon mechanics are unchanged; this supersedes earlier fixed-HUD meter notes.
