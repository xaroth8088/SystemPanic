# Bloom Siege: weapon

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

The weapon owns two nonblocking nectar wells, a watering can and plants. Stand still at a well with Fire released to refill at two nectar/second. Hold Fire to sow spaced seeds and water the nearest growing plant within 95px; a mature plant consumes one nectar over about 1.18s. Time alone never grows seeds. Release triggers blooms; growth below 0.2 is harmless. The can starts empty with capacity four, gains two capacity per pickup (maximum 24), and retains water across levels. Nectar wells supply no healing. Register wells using world.set_geometry(self, wells); recreate on level/obstacle changes and clear on deactivation. This keeps the weapon independently copyable with foreign obstacles. Pickups change capacity only, never current water or blast damage. Readout includes a moving can icon, numeric meter, refill and empty cues. Demo controls refill and spend real water through normal inputs.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

Pools now vary both coordinates every level. A private seed/level RNG samples left/right horizontal regions and three cycling vertical bands, so the route changes without combat RNG consumption or dependence on level history. Geometry-safe relocation still applies. The whole pilot must be outside every 42px pool before sowing (center distance > 42 + pilot.radius). This only blocks new plants; watering existing nearby plants remains allowed. Refill still requires standing still and releasing Fire. Readout explains the leave-pool requirement, and QA leaves the pool after filling before planting.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

## Arcade feedback (2026-10-26)

Bloom damage now rewards growth non-linearly: 8+112*growth**2.4 (maximum 120). Radius is 28+70*growth (maximum 98, formerly 167); cascade reach is radius+20 (formerly radius+45). Growth below .2 is still harmless. Nectar cost, can capacity-only upgrades and manual watering remain unchanged. Instruction prose/facing dot are removed; the can icon and numerical nectar meter remain.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).

## Quiet presentation and tail routing (2026-10-28)

Fixed top-left heat, speed, charge, energy, battery, nectar and cooldown readouts are removed. This role retains its attacks and existing on-pilot physical/charge/resource feedback where applicable. Empty readout scheduling/helpers were removed when they served no other presentation. Weapon mechanics are unchanged; this supersedes earlier fixed-HUD meter notes.
