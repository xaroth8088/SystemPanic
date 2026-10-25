# Orbit Keeper Pak

Read [Pak authoring memory](../AGENTS.md). Complete API 4 Pak: Hold the orbit. Returning glaives cut through circling sentinels.

The six role folders own their classes, assets and gameplay rules. Actor factories own stats, weapons own cadence, and local projectile/death callbacks own their mechanics. Core primitives do not interpret traits. Preserve independent play, compatible mixtures and recorded original AI provenance.

Sentinels rotate/fire faster and shift their formation toward the pilot while leading shots. Satellite generators rotate an elliptical field around the central plinth.

Special now toggles _fire_outward along with reversing orbit and shielding, once per accepted press. aim_direction uses the actual player-to-center radial vector; status reports FIRE INWARD/OUTWARD. All shipped weapons respect this intent; the glaive reaches 600 px/s outbound and retains its existing return timing. Demo controls line up radial shots, choose inner/outer safe spacing and predict threats using ordinary input.

Current package behavior: Step between orbital rings and toggle radial fire. Glaives return from offscreen; orbiting cores upgrade them. The weapon folder owns powerup.py and its upgrade formulas; the engine owns the tenth-kill cadence and shared pickup count.
