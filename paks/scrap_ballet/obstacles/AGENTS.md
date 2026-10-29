# Scrap Ballet: obstacles

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Drifting destructible satellite debris and nonblocking magnetic fields are local terrain. Fields attract and swirl bodies through world.move_body. A separate seed/level RNG builds fresh objects; moving debris repairs overlaps.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.
