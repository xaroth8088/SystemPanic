# Pulse Abbey: pilot

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Eight-way digital movement; an edge-triggered 2.6-second bell step grants a short fast protected move. Status shows step recovery; the weapon owns its independent beat cue. The demo uses keyboard/D-pad directions, without analog steering.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

Facing refinement: the local pilot sheet is 8 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/SE/S/SW/W/NW/N/NE. Original built-in imagegen source: assets/images/pulse_abbey-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection.
