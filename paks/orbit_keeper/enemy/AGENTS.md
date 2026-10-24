# Orbit Keeper: enemy

Read [this Pak's memory](../AGENTS.md) and [the public ABCs](../../../src/system_panic/pak_api.py). `enemy.py` subclasses `EnemyBase`. Required methods: `advance_enemy(world, enemy, dt), sprite(world, entity=None)`. `family` and `splits` describe enemy state. The engine advances age/timer first.

Load local handles in `init()` with `self.load_asset(filename)`. Their attribute names are private choices. Instances belong to one run; use the explicit lifecycle methods for world setup and sound cleanup. Drawing/track selection cannot advance simulation. These files can be copied as a partial component. Keep generated-asset provenance when replacing content.
