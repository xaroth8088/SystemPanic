# Kite pilot

Digital steering adds acceleration; passive drag is 2.9/s with speed capped at255. Hold special uses 10/s drag, speed cap130 and firmer steering. Anchoring grants no invulnerability. Geometry contacts remove only inward velocity. The kite selects upright eight-bearing poses from deliberate movement intent. Arrival/swap protection, damage recovery and +12 level healing belong here. Demo policy emits ordinary eight-direction Controls.


## True directional presentation

The current sheet uses 8 actual facing columns and four animation rows. East starts at column0; free-moving actors proceed clockwise through SE/S/SW/W/NW/N/NE, while Canopy uses East/West. Sprite selection uses the shared actor angle; sprite_angle returns zero and sprite_flip_x returns false. Original source poses and prior-row snapshots are recorded in pak.json authoring metadata and asset ledgers. Drawing must not mutate simulation or RNG.
