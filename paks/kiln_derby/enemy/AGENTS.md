# Kiln golems

The upright golem periodically commits a predicted pursuit heading, then runs/tacks toward the pilot. Eight authored bearing poses keep the golem upright without runtime rotation or mirroring. Active ash projectiles begin at level3 and have no windup/target graphics. Movement, local difficulty, contact damage, health/rewards all stay here. Geometry obstruction chooses a side slide. ash.py schedules its own flight/collision/lifetime and exposes threat intent only to QA policies.


## True directional presentation

The current sheet uses 8 actual facing columns and four animation rows. East starts at column0; free-moving actors proceed clockwise through SE/S/SW/W/NW/N/NE, while Canopy uses East/West. Sprite selection uses the shared actor angle; sprite_angle returns zero and sprite_flip_x returns false. Original source poses and prior-row snapshots are recorded in pak.json authoring metadata and asset ledgers. Drawing must not mutate simulation or RNG.
