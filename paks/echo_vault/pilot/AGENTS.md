# Echo Vault: pilot

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

The bounded history records active simulation time and position. Rewind restores only a safe past position plus short protection, never health, score, enemies, kills or projectiles. Clear history at level/shuffle boundaries. The digital demo evades public projectile threats and uses rewind when threatened.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

Facing refinement: the local pilot sheet is 8 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/SE/S/SW/W/NW/N/NE. Original built-in imagegen source: assets/images/echo_vault-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection.
