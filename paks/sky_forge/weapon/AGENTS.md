# Sky Forge: weapon

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). This folder owns all behavior/helpers/assets; copy the whole folder as a partial Pak. No sibling-role private state or other Pak imports. Use public world/body/shape contracts. Drawing and sprite selection cannot change simulation or RNG.

Tap/release below .55s to stab (25+6n damage, 72+min(36,4n) reach, .13s active). Hold .55–1.3s and release to throw the single sword: strength s gives 90+50s+18n damage, speed 620+220s, and gravity 160. The first enemy, solid surface, border or 1.6s flight limit drops the blade; resting gravity is 550. No automatic return or expiry: physically collect it before attacking again. A locked weapon reinserts its unclaimed blade after host projectile cleanup and relocates it safely on terrain/level changes; replacement discards it. Recovery is .28s. Drawing and charge hints are read-only.

The local sheet has four horizontal animation frames. Pickups capture the raw local ImageAsset and select their own frame when drawn, so provider changes cannot break them. The engine owns tenth-kill scheduling and the persistent collected count; powerup.py owns movement/pickup/expiry and this weapon interprets the count.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

## Arcade feedback (2026-10-26)

Short release now makes a 0.22s overhead Swing: its right-facing blade sweeps from -0.85pi to +0.25pi, mirrored for left facing. Sampled swept rays stop at actual filtered cover; enemies take 25+6n once and surviving targets are pushed 28px through collision checks with a 95px/s impulse. Existing stab reach formula and charged throw/retrieve ownership remain. The dropped-blade arrow and instructional prose are removed; a charge meter and actual blade remain. Resting blade art anchors its visible bottom at its physical feet. QA commits to a complete ordinary-input walk off a support to retrieve a blade below, including an overhung deck lip.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).

## Quiet presentation and tail routing (2026-10-28)

Fixed top-left heat, speed, charge, energy, battery, nectar and cooldown readouts are removed. This role retains its attacks and existing on-pilot physical/charge/resource feedback where applicable. Empty readout scheduling/helpers were removed when they served no other presentation. Weapon mechanics are unchanged; this supersedes earlier fixed-HUD meter notes.
