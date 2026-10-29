# Neon Breach: music

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Renewal: the local soundtrack uses its registered prepared master. Eleven of the initial twelve loops have explicit source regions and cyclic joins; Sky Forge retains its existing healthy master. Source WAVs are preserved; assets/audio/prepared.json records operations and hashes.

Playtest refinement: preserve the generated WAV and select source seconds [0,20.8], ahead of the fade starting around 21s. The existing .18s cyclic crossfade produces a 20.62s encoded loop. Check the entire four-second join neighborhood, including the crossfade inside the file start; testing only the exact endpoint missed the earlier fade.
