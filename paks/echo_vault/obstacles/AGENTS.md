# Echo Vault: obstacles

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Level-seeded shutters alternate between blocking and open phases. Closing is visibly warned; only closing walls require overlap repair. Terrain phase is private active-time state and does not advance during paused/clear screens.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.
