# Pulse Abbey: weapon

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Minimum charge 0.45s, maximum 1.2s, recovery 0.3s. Invalid releases reset charge and fizzle without creating Resonance. Gold judgement remains the 0.6s simulation beat; readout distinguishes undersized charge and ready releases. Upgrades never bypass the minimum. Full rings hit each target once and perfect rings parry through the public threat query.

Current reach is 70 + 110*charge_strength + min(240, pickups*20): an unupgraded full charge reaches 180px, compared with the previous 420px. Pickups add 20px each up to 240px bonus. Clamp the final expanding ring to reach before hit tests, including a large dt. Damage is (18 + 50*strength + pickups*5) times 1.6 on gold or 0.2 offbeat, so an offbeat pulse deals one eighth of the matching gold pulse. QA approaches within 125px using ordinary digital controls to suit the compact starting range.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).
