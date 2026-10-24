# Void Drifter: pilot

Read [this Pak's memory](../AGENTS.md) and [the public ABCs](../../../src/system_panic/pak_api.py). `pilot.py` subclasses `PilotBase`. Required methods: `move(world, dt, control, jump, special), sprite(world, entity=None)`. `controls`, `special`, and optional `activate`/`demo_controls` belong here.

Load local handles in `init()` with `self.load_asset(filename)`. Their attribute names are private choices. Instances belong to one run; use the explicit lifecycle methods for world setup and sound cleanup. Drawing/track selection cannot advance simulation. These files can be copied as a partial component. Keep generated-asset provenance when replacing content.
