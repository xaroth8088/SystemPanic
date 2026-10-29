# Fold gates and shutters

Private seeded layouts create four nonblocking paired gates and two moving shutters each level. Only actor centers within 21+0.35*radius activate a gate; arrival is offset along the exit bearing, constrained with safe_position(body=...), and velocity rotates without changing magnitude. An obstacle-owned id/body lifetime map prevents ping-pong for 0.85s and prunes despawned bodies. Foreign pilots/enemies are treated identically through public state. No actor private fields or identity traits are used.

Positive hit_cover damage opens a shutter for 1.25s without reducing its finite sentinel health. Open shutters pass bodies and shots; closing/moving overlap repairs use public real geometry. Gates render the local animated opening arch plus pair-colored diamond; body/collision state is never updated by drawing. Procedural build consumes no combat RNG and returns fresh objects.
