# Echo Vault: enemy

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Chronoguards predict movement, mark delayed danger zones, then fire toward that prediction. Later levels add bounded flank blinks. They do not inspect rewind history or react to input device types.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

## Quiet presentation and tail routing (2026-10-28)

Advance attack/recovery/aim marker objects are removed. Creature animation, target locking, attack timing, movement, vulnerability and damage rules remain local and unchanged. Delayed damage areas are invisible before activation; actual active hazards/projectiles still render. Only creature teleport destination warnings remain elsewhere. This supersedes earlier cue-presentation notes; see the Pak-wide presentation memory.

## Temporal impact clarity (2026-10-28)
The old red circles were delayed damaging bursts at the predicted player position, not teleport destinations. Zone now fills the active damage footprint, expands a pale shock ring, draws broken clock spokes and briefly connects the impact to the caster's recorded source. The .72s invisible delay, .35s damage window, damage and radius are unchanged. No advance warning is reintroduced. Reduced motion keeps a steady inner ring.

At wave four onward, a successful flank blink appends BlinkEcho only after relocation: a faded departure sprite, arrival ring and optional thin trail expire after .28s. The caster's ordinary sprite remains at its actual position. Both effects are role-local and drawing consumes no RNG or gameplay state. Source/frozen screenshots and tests are recorded in [verification memory](../../../tests/AGENTS.md).
