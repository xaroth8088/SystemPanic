# Glasswake: enemy

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Bolt now substeps motion at no more than 2px per step, reflects from arena borders and projectile-blocking actual shape overlaps, and damages the pilot once before removal. Body-only rails remain transparent. Cover damage still uses world.hit_cover. Lifetime is six active seconds with sixteen allowed bounces; foreign curves use a local approximate axis normal.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

## Quiet presentation and tail routing (2026-10-28)

Advance attack/recovery/aim marker objects are removed. Creature animation, target locking, attack timing, movement, vulnerability and damage rules remain local and unchanged. Delayed damage areas are invisible before activation; actual active hazards/projectiles still render. Only creature teleport destination warnings remain elsewhere. This supersedes earlier cue-presentation notes; see the Pak-wide presentation memory.
