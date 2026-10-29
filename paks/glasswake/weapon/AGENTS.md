# Glasswake: weapon

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

The local ray traces actual projectile-filtered shape overlap, with approximate axis normals for foreign curves. Damage is (37 + 9*pickups) * 3**reflection * dt, once per target per step, retaining bounded extra reflections and heat recovery. Banking is deliberately much stronger than direct fire.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).
