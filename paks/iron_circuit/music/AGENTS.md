# Iron Circuit: music

Read [this Pak's memory](../AGENTS.md) and [the public ABCs](../../../src/system_panic/pak_api.py). `music.py` subclasses `MusicBase`. Required methods: `track(world=None)`. Return a local sound handle or None for silence. The engine owns streaming/music volume.

Load local handles in `init()` with `self.load_asset(filename)`. Their attribute names are private choices. Instances belong to one run; use the explicit lifecycle methods for world setup and sound cleanup. Drawing/track selection cannot advance simulation. These files can be copied as a partial component. Keep generated-asset provenance when replacing content.
