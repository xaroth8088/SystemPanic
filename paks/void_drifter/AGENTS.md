# Void Drifter Pak

Read [Pak authoring memory](../AGENTS.md). Complete API 4 Pak: Master momentum. Pierce drifting rocks before they fracture.

The six role folders own their classes, assets and gameplay rules. Actor factories own stats, weapons own cadence, and local projectile/death callbacks own their mechanics. Core primitives do not interpret traits. Preserve independent play, compatible mixtures and recorded original AI provenance.

Asteroids and faster fragments gain speed, stronger pursuit and predictive targeting. Debris generators vary sparse island positions/sizes and add a few islands at later levels.

Current package behavior: Drift among debris, black holes and crossing comets. Collect drifting cores to upgrade the lance. The weapon folder owns powerup.py and its upgrade formulas; the engine owns the tenth-kill cadence and shared pickup count.
