# Pressure kiln

Fire raises pressure.28/s; release/lockout cools.72/s. Cadence tightens from.34 to.25s. Pressure cap vitrifies the nozzle for.9s. Four pips attach to the player only while hot/locked; no fixed HUD readout.

Marbles carry captured art, heat, damage, rebounds and hit IDs. They integrate in<=4px substeps, using blocks_projectile separately from body filtering; foreign body-only rails pass shots. Hot contact rebounds lose heat and permit another hit after a bounce. Heat<=.08 or exhausted rebounds shatter. Low-heat enemy impact shatters in a28px burst. Upgrades add damage and up to3 rebounds. Scheduled nozzle references are pruned after host clears. powerup.py captures local raw art/chime for50s independent drops.
