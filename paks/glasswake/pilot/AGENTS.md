# Glasswake: pilot

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Gliding interpolation and a quarter-turn dash are pilot-local. The dash retains its turned heading for the whole burst even if the original direction stays held; a regression checks this. Demo routing goes above/below blocking mirrors and steps around their corners; it also evades public hostile trajectories. This prevents the reproduced post-level-one demo stall. Inputs are quantized to keyboard/D-pad directions.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

Facing refinement: the local pilot sheet is 8 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/SE/S/SW/W/NW/N/NE. Original built-in imagegen source: assets/images/glasswake-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection.
