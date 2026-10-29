# Scrap Ballet: pilot

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Thrust, drag, speed limits, boundary/geometry reflection and magnetic braking belong here. Braking is edge-triggered and pushes nearby enemies using neutral movement services. The demo uses digital directions.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

Facing refinement: the local pilot sheet is 8 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/SE/S/SW/W/NW/N/NE. Original built-in imagegen source: assets/images/scrap_ballet-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection.
