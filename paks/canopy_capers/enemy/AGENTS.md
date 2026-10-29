# Canopy enemies and platform navigation

Lantern beetles have radius14 and28+3.2*wave health. Spawn selection uses actual public rectangular supports (plus floor), spreads bodies between elevations and leaves a3px settling gap. Enemy create/adoption still respects the caller's suggested position. Contact difficulty, kill/level scores and effects belong here.

navigation.py owns a bounded surface graph and ballistic reach planning at gravity900, jump460 and at most250 horizontal air speed. Walk speed grows locally from112 toward150 with difficulty scaling. It probes each candidate top through the public body filter; only the inherited rectangle overlap method qualifies as a platform. Custom shape rects remain broad-phase metadata. Cheap reach edges are shared in at most8 immutable snapshots; dense foreign layouts consider at most16 nearby platforms plus the floor. The chosen jump is sampled against all actual geometry/body filters before committing, with alternative edge launches for solid decks. Failure temporarily excludes that edge rather than bypassing collision.

A committed jump steers toward its real descending landing point and retains spring-supplied vertical velocity. Walk-off descent commits beyond a ledge until below its catch zone. Floor pursuit periodically chooses reachable elevated flanking routes; it does not immediately erase every platform spawn into a floor pile. Leaf disappearance invalidates targets through public filtering, and the next landing replans. No sibling pilot counters or obstacle kind/missing fields are read.

Both original East/West columns animate across four rows. Render size40 at radius14 keeps the new wide beetle's opaque feet/top near its collision surface; all8 poses are tested. Read-only drawing changes no state/RNG.

Tests execute actual stepping onto three authored deck heights while leaves collapse/regrow, climb solid stairs and descend again without teleport-sized displacement, distribute spawns over five elevations, and show six floor-spawned beetles taking multiple flanking supports. Thirty procedural probes additionally reach the highest authored support through level101. Arbitrary foreign custom geometry remains correctly collidable but is not promised to be navigable as a platform graph.


## True directional presentation

The current sheet uses 2 actual facing columns and four animation rows. East starts at column0; free-moving actors proceed clockwise through SE/S/SW/W/NW/N/NE, while Canopy uses East/West. Sprite selection uses the shared actor angle; sprite_angle returns zero and sprite_flip_x returns false. Original source poses and prior-row snapshots are recorded in pak.json authoring metadata and asset ledgers. Drawing must not mutate simulation or RNG.
