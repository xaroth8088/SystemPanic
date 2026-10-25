# Vector Coil: pilot

Read [this Pak](../AGENTS.md), [Pak contracts](../../AGENTS.md) and [public ABCs](../../../src/system_panic/pak_api.py).

This folder owns its component code, helpers and generated assets. Use explicit ABC callbacks, local handle names and private timing/state. Do not import another Pak's module or move content rules into core. Drawing and asset selection cannot change simulation/RNG. Copy the entire role folder when making a partial. Assets are generated outside the game; provenance is recorded in assets/manifest.json.

Continuous cardinal movement makes right-angle trails. The special reverses with a short turn lock. Trail contacts deal damage once per enemy per step; one scheduled TrailImage draws the retained points rather than spawning particles every frame.
