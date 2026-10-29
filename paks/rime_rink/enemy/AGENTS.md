# Rime eels

Eels pursue with a locally scaled target speed, predictive aim, sinusoidal heading and short obstacle probes. Velocity blends toward desired motion so curling/press impulses persist rather than disappearing in one step. Body collisions bank velocity. Enemy health29+3.5*wave and contact difficulty policy grow locally; score/bursts belong here. No foreign geometry internals are inspected.


## True directional presentation

The current sheet uses 8 actual facing columns and four animation rows. East starts at column0; free-moving actors proceed clockwise through SE/S/SW/W/NW/N/NE, while Canopy uses East/West. Sprite selection uses the shared actor angle; sprite_angle returns zero and sprite_flip_x returns false. Original source poses and prior-row snapshots are recorded in pak.json authoring metadata and asset ledgers. Drawing must not mutate simulation or RNG.
