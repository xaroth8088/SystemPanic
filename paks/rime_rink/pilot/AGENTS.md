# Rime pilot



Digital directions accelerate510px/s² with low.65 exponential drag and290 speed cap. Diagonals are normalized. Hold X to carve:7.5 drag,720 acceleration and115 cap; only the brake entry plays the local sound. Collisions reflect inward normal velocity with.55 restitution. No analog-speed or device-specific rules exist.



Pilot-local damage protection lasts.85s; arrival/swap protection and14 level recovery are local policy. QA chooses ordinary digital pursuit/orbit/retreat, anticipates momentum and brakes near enemies. Tests compare braking and cardinal/diagonal acceleration magnitudes.



## True directional presentation

The current sheet uses 8 actual facing columns and four animation rows. East starts at column0; free-moving actors proceed clockwise through SE/S/SW/W/NW/N/NE, while Canopy uses East/West. Sprite selection uses the shared actor angle; sprite_angle returns zero and sprite_flip_x returns false. Original source poses and prior-row snapshots are recorded in pak.json authoring metadata and asset ledgers. Drawing must not mutate simulation or RNG.
