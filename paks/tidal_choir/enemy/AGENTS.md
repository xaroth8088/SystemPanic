# Tidal Choir: enemy

Read [Pak memory](../AGENTS.md) and [Pak contracts](../../AGENTS.md).

Cuttlefish separate from nearby peers, swim with inertia, lock a windup target, then jet charge. Later charges leave delayed ink danger zones. The windup is more vulnerable to attacks; neither buoyancy nor bubble policy is interpreted by the host.

Assets/helpers stay inside this role. Sprite selection is read-only and uses the four-frame local row. Input devices and mapping belong to the shell. See [verification memory](../../../tests/AGENTS.md) for actual evidence and remaining limits.

## Quiet presentation and tail routing (2026-10-28)

Advance attack/recovery/aim marker objects are removed. Creature animation, target locking, attack timing, movement, vulnerability and damage rules remain local and unchanged. Delayed damage areas are invisible before activation; actual active hazards/projectiles still render. Only creature teleport destination warnings remain elsewhere. This supersedes earlier cue-presentation notes; see the Pak-wide presentation memory.

## Ink attack clarity (2026-10-28)
The former red circle/X represented damaging ink left at the charge departure point from level five onward. Zone now fills that footprint with a dark violet stain, overlapping lobes and drifting flecks. It still waits invisibly for .6s, hurts within the same 55px radius for .8s and then disappears. Damage, jet speed/timing, target locking and AI are unchanged.

Enemies.draw adds a wake only behind an actual charge in progress; later-level wakes include violet ink droplets matching the cloud. Seek/windup draws have no new marker or target/path warning. The role owns all new rendering. Cached stains are bounded by a sixteen-entry LRU and never modified when drawn; animation uses existing age, never gameplay RNG. Reduced motion keeps cloud texture and wake offsets steady. See [verification memory](../../../tests/AGENTS.md) and docs/tidal-ink.json for source/frozen results and limits.
