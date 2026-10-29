# Canopy pilot

Primary Controls.fire now triggers jump on a rising edge; Up is a separate optional edge alias. Held primary never repeats a jump on landing. Owns run speed245, gravity900, two jumps at-430 and terminal descent580. X starts1.05s leaf glide on an edge with2.8s cooldown; glide gravity/terminal descent are260/115 and run speed220. The weapon independently owns automatic stomp contact, damage and rebound; no weapon-private state is queried.

Flat feet snap only to inherited Cover rectangle overlap methods after evaluating the body's public filter. Custom shapes retain generic motion/callbacks. All eight original East/West-by-four frames keep opaque boot bottoms at player.pos.y+radius16; no rotated or mirrored standing poses are synthesized. Damage protection, level recovery and swap protection stay local.

QA emits ordinary primary-button edges, not privileged movement. It can commit to a reachable intermediate rectangular support before attempting a higher double jump, release before a second jump, avoid side contact, and walk off supports to descend. An unreachable waypoint is discarded on grounding; spring-column exits include the full circle corner footprint. Actual gameplay has no auto-navigation.


## True directional presentation

The current sheet uses 2 actual facing columns and four animation rows. East starts at column0; free-moving actors proceed clockwise through SE/S/SW/W/NW/N/NE, while Canopy uses East/West. Sprite selection uses the shared actor angle; sprite_angle returns zero and sprite_flip_x returns false. Original source poses and prior-row snapshots are recorded in pak.json authoring metadata and asset ledgers. Drawing must not mutate simulation or RNG.
