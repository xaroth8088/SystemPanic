# Inertial tug

Eight digital thrust directions, exponential drag and a 255px/s maximum. X edge reverses 65% of current velocity, flips a local displayed polarity and pushes nearby enemies through world.move_body; no damage is granted by that pulse. Local protection/cooldown/heal/defeat policies stay here. The pilot does not inspect obstacle fields or any sibling state. Local eight-bearing/four-phase art selects deliberate thrust direction without runtime rotation or mirroring. QA uses ordinary digital inputs and real blockers.


## True directional presentation

The current sheet uses 8 actual facing columns and four animation rows. East starts at column0; free-moving actors proceed clockwise through SE/S/SW/W/NW/N/NE, while Canopy uses East/West. Sprite selection uses the shared actor angle; sprite_angle returns zero and sprite_flip_x returns false. Original source poses and prior-row snapshots are recorded in pak.json authoring metadata and asset ledgers. Drawing must not mutate simulation or RNG.
