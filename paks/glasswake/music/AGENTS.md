# Glasswake: music

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

The original 32s Stable Audio source is unchanged. tools/assetforge/prompts.json explicitly selects source seconds [0,30] before the existing 0.18s cyclic overlap. The shipped OGG is 29.82s. This removes the generated faded/silent outro rather than adding runtime silence skipping. Hashes/processing are recorded in the existing ledgers.

Assets/helpers stay inside this role. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.
