# Ceramic racer

Normal speed225 follows normalized digital input with10/s convergence. Special edge banks the current direction for a.22s550px/s dash (2.1s cooldown,.26s protection). Wall normals remove inward velocity. Arrival/swap protection, damage recovery, +12 level healing and defeat burst are local. Demo policy uses ordinary eight-direction inputs and avoids nearby projectile threats.


## True directional presentation

The current sheet uses 8 actual facing columns and four animation rows. East starts at column0; free-moving actors proceed clockwise through SE/S/SW/W/NW/N/NE, while Canopy uses East/West. Sprite selection uses the shared actor angle; sprite_angle returns zero and sprite_flip_x returns false. Original source poses and prior-row snapshots are recorded in pak.json authoring metadata and asset ledgers. Drawing must not mutate simulation or RNG.
