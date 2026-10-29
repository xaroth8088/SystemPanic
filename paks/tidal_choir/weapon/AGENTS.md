# Tidal Choir: weapon

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Only bubbles with release radius at least 30px (0.6s charge) can entrain enemies or deal burst damage. Smaller bubbles drift and pop harmlessly, even after upgrades. The weapon readout marks the minimum charge. Pickups improve powered burst size/damage without bypassing this threshold. Tethered bubbles follow the pilot without pulling enemies. Powered flight lasts up to 1.35s; powerless flight 0.65s. Every burst uses a per-ID hit set. Host-cleared tether references are pruned before replacement.

Screen borders no longer trigger a burst. Released bubbles clamp inside the radius-aware screen bounds, reflect outward velocity and retain 65% of their full velocity per rebound. A corner reflects both axes and damps once. Buoyancy continues after contact; the existing timed fuse still bursts powered bubbles after 1.35s (small harmless bubbles after 0.65s), without resetting age on a bounce. Tests cover all four edges, a corner, reduced speed and eventual fuse expiration.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).
