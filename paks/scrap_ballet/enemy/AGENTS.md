# Scrap Ballet: enemy

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Rival tugs lead moving players, circle with inertia, wind up and commit to ramming. Exit the charge state before its timer can restart another charge. Geometry normals reflect velocity; the host has no tug rules.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

## Quiet presentation and tail routing (2026-10-28)

Advance attack/recovery/aim marker objects are removed. Creature animation, target locking, attack timing, movement, vulnerability and damage rules remain local and unchanged. Delayed damage areas are invisible before activation; actual active hazards/projectiles still render. Only creature teleport destination warnings remain elsewhere. This supersedes earlier cue-presentation notes; see the Pak-wide presentation memory.
