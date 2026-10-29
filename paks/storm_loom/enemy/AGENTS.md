# Storm moths

Moths tack across pursuit then accelerate in their 2.7s cycle. Shared velocity remains available for outside wind/reeling. Contact attack and level-scaled health/speed are local. Spawn placement is bounded and asks for230px clearance. An obstructed moth changes tack and slides around the hub; no engine navigation trait or extra child spawns.


## True directional presentation

The current sheet uses 8 actual facing columns and four animation rows. East starts at column0; free-moving actors proceed clockwise through SE/S/SW/W/NW/N/NE, while Canopy uses East/West. Sprite selection uses the shared actor angle; sprite_angle returns zero and sprite_flip_x returns false. Original source poses and prior-row snapshots are recorded in pak.json authoring metadata and asset ledgers. Drawing must not mutate simulation or RNG.
