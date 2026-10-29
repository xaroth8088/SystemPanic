# Burrow Patrol: weapon

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). This folder owns all behavior/helpers/assets; copy the whole folder as a partial Pak. No sibling-role private state or other Pak imports. Use public world/body/shape contracts. Drawing and sprite selection cannot change simulation or RNG.

Finite reach min(300,145+18n), pressure .85+.08n/s, gradual damage 7+2n/s, pop max(45,1.25*max_health). A pop has .32s pump recovery. Releasing/missing drains pressure; changing target resets it. PressureLine is visual only and recreates after cleanup.

The local sheet has four horizontal animation frames. Pickups capture the raw local ImageAsset and select their own frame when drawn, so provider changes cannot break them. The engine owns tenth-kill scheduling and the persistent collected count; powerup.py owns movement/pickup/expiry and this weapon interprets the count.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).

2026-10-28: PressureLine's fixed top-left pressure/charge bar is removed. Its tether, endpoint ring and expanding weapon sprite still communicate the actual pump action; reach, pressure, pop damage and recovery are unchanged. The visual-cleanup test includes PressureLine so it checks this effect as well as the generic readout helpers.
