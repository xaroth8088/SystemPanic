# Rivet skiffs

Local Skiff bodies curve toward a predicted pilot position, with alternating bank directions. Solid collision reflects shared velocity and switches banking; generic obstacle forces can modify velocity afterward. Health/contact damage grow indefinitely; movement approaches a cap. The role owns difficulty interpretation, safe bounded placement, rewards and death feedback. Local eight-bearing/four-phase art selects actual velocity direction without runtime rotation or mirroring.


## True directional presentation

The current sheet uses 8 actual facing columns and four animation rows. East starts at column0; free-moving actors proceed clockwise through SE/S/SW/W/NW/N/NE, while Canopy uses East/West. Sprite selection uses the shared actor angle; sprite_angle returns zero and sprite_flip_x returns false. Original source poses and prior-row snapshots are recorded in pak.json authoring metadata and asset ledgers. Drawing must not mutate simulation or RNG.
