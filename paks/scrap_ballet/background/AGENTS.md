# Scrap Ballet: background

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Procedural scenery is read-only presentation. draw must never change active simulation state or consume gameplay RNG.

Assets/helpers stay inside this role. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.
