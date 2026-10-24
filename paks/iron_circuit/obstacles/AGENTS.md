# Iron Circuit: obstacles

Read [this Pak's memory](../AGENTS.md) and [the public ABCs](../../../src/system_panic/pak_api.py). `obstacle.py` subclasses `ObstaclesBase`. Required methods: `build(), sprite(world, entity=None)`. Return fresh Cover objects from build(). Collision layout is independent of the background.

Load local handles in `init()` with `self.load_asset(filename)`. Their attribute names are private choices. Instances belong to one run; use the explicit lifecycle methods for world setup and sound cleanup. Drawing/track selection cannot advance simulation. These files can be copied as a partial component. Keep generated-asset provenance when replacing content.
