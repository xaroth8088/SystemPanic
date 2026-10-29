# Scrap Ballet: weapon

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Initial scrap uses a private seed/level RNG and is created during on_level_start/on_shuffle, never by holding Fire. The optional on_enemy_destroyed notification adds three pieces for any enemy provider. Debris cap 64; orbit cap 3 + min(3, pickups//2). Attracted free pieces must physically reach the pilot. Only launched pieces damage, once before settling back to recoverable loose debris; time/bounce expiry also settles rather than deletes ammo. Prune host-cleared references and reseed after a swap. Weapon demo_controls seeks real debris through ordinary digital input.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).
