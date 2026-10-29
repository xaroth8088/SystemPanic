# Reversible pylons and induction rails

Private seeded generator returns three true circular solid pylons and two short body-blocking, shot-passing rails. Pylon circle/segment overlap and navigation_key describe the same collision shape; a rectangle is only its broad-phase bound. All bodies within 135px receive the same signed field force through public movement and velocity. Moving projectile velocity bends while preserving speed; stationary regions are ignored. Projectiles still own integration/damage/lifetime.

Positive hit_cover damage reverses a pylon with 0.35s burst debounce and preserves finite sentinel health. Fields are always mechanically active; their quiet arcs show actual force range rather than future danger. No shape reads another component's private state. Draw/build never consume combat RNG; each level has fresh geometry.

Integration variation check: pylons independently jitter both axes and rails vary y/length, retaining broad corridors. The standard 20-seed/level signature matrix now stays distinct and repeatable with no combat RNG use (tests/test_levels.py layout method).
