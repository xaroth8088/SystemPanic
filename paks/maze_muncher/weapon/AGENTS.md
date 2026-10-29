# Maze Muncher: weapon

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). This folder owns all behavior/helpers/assets; copy the whole folder as a partial Pak. No sibling-role private state or other Pak imports. Use public world/body/shape contracts. Drawing and sprite selection cannot change simulation or RNG.

Forward swept lunge 460 px/s for .14+min(.08,.008n), damage 20+5n, cooldown max(.3,.62/(1+.035n)). Hitting a foe moving away in the lunge direction deals x1.75. One hit ends the dash, separates both bodies through move_body, and grants .22s safe separation. No attack projectile is launched.

The local sheet has four horizontal animation frames. Pickups capture the raw local ImageAsset and select their own frame when drawn, so provider changes cannot break them. The engine owns tenth-kill scheduling and the persistent collected count; powerup.py owns movement/pickup/expiry and this weapon interprets the count.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

Playtest refinement: obstacles build a fresh seeded 30×15 maze of 32px tiles, with DFS passages, braided alternate routes, a central room and an open row-seven east/west tunnel. Both local actors and the weapon’s lunge/knockbacks wrap x; vertical borders remain solid. Grid centers are 16+32k. Independently copied pilot/enemy navigation uses actual shape filters and horizontal wrap links. Off-grid knockbacks recover by completing the small alignment leg before following a corridor; finite-step corner correction remains collision-checked. This prevents nearest-cell reversal stalls without changing the Controls contract.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).

## Quiet presentation and tail routing (2026-10-28)

Fixed top-left heat, speed, charge, energy, battery, nectar and cooldown readouts are removed. This role retains its attacks and existing on-pilot physical/charge/resource feedback where applicable. Empty readout scheduling/helpers were removed when they served no other presentation. Weapon mechanics are unchanged; this supersedes earlier fixed-HUD meter notes.
