# Echo Vault: weapon

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Each held-fire cadence records an origin and direction for delayed volleys. Assisted targeting leads the initial shot; recorded echoes retain their original vector after movement/rewind. Upgrades add damage and bounded additional repeats. Local scheduled objects own delay, motion, piercing and terrain hits.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).
