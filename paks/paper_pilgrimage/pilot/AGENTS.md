# Paper glider

Inertial eight-direction digital movement (235px/s target). X edge starts a 0.2s, 620px/s committed fold at the latest deliberate movement bearing; 2.4s cooldown. Direction changes during that fold do not steer it. A short local protection window accompanies the fold; arrival/swap protection, damage recovery and per-level healing are local policies. No weapon or obstacle private state is read. Eight authored bearing columns each contain four animation phases; heading selects a pose without runtime rotation or mirroring. QA routes around actual body-blocking geometry with ordinary digital Controls.


## True directional presentation

The current sheet uses 8 actual facing columns and four animation rows. East starts at column0; free-moving actors proceed clockwise through SE/S/SW/W/NW/N/NE, while Canopy uses East/West. Sprite selection uses the shared actor angle; sprite_angle returns zero and sprite_flip_x returns false. Original source poses and prior-row snapshots are recorded in pak.json authoring metadata and asset ledgers. Drawing must not mutate simulation or RNG.
