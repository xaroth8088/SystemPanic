# Vector Coil: weapon

Read [this Pak](../AGENTS.md), [public ABCs](../../../src/system_panic/pak_api.py) and [Pak contracts](../../AGENTS.md). This folder owns all behavior/helpers/assets; copy the whole folder as a partial Pak. No sibling-role private state or other Pak imports. Use public world/body/shape contracts. Drawing and sprite selection cannot change simulation or RNG.

A new loop of area >=900 captures fully contained enemy circles. Baseline live tails bounce without damage. Upgrades add 4n contact damage per enemy per .4s, width 2+min(6,.5n) and length 6000+500n. Filled solid territory has a walkable boundary, lasts 22 active seconds, and dims in its last four seconds. This avoids permanent capture dead ends. Level/removal clears owned geometry; unrelated presentation swaps preserve it for its remaining lifetime.

The local sheet has four horizontal animation frames. Pickups capture the raw local ImageAsset and select their own frame when drawn, so provider changes cannot break them. The engine owns tenth-kill scheduling and the persistent collected count; powerup.py owns movement/pickup/expiry and this weapon interprets the count.

Pickup audio: init loads the role-local pickup.ogg. The factory captures its SoundAsset in the drop, alongside the art. powerup.update plays it once at volume .45 only when world.collect_powerup returns True; expired, unregistered and repeated updates stay silent. The originating drop keeps its sound after a weapon/level change. Playback uses the ordinary effects bus and mute/volume settings.

Playtest refinement: a live path anchored on an existing capture can close against its connected boundary network. network.py splits old edges at anchors/intersections and finds a connected boundary path; new open edges plus that path define the capture polygon. Disconnected old regions do not connect, walking only old outlines does not recapture, and expired regions leave the network. Whole-circle containment, 900px² minimum and 22s region lifetime still apply.

Presentation: in-arena control prose and redundant facing indicators are removed; actual attacks, meters and numerical resources remain. See [Pak presentation memory](../../AGENTS.md).

## Quiet presentation and tail routing (2026-10-28)

LiveLine.navigation_key captures class/endpoints/width; CarvedArea.navigation_key captures class/polygon/inset. These opt-in immutable collision snapshots allow external navigation to share exact graphs across equal recreated shapes. Color, owner response state and fading lifetime do not change circle overlap. No tail rules, collision response or capture policy moved into the host.

Long curved captures retain hundreds of source vertices. CarvedArea now indexes exact edge candidates by rows/cells for odd-even interior and inset-distance queries; a full point snapshot detects edits before reuse. It still calls the original closest-point math and keeps strict contact inequalities. Boundary anchors reject only bounds farther than their tolerance, and boundary-network splitting considers spatially intersecting candidate pairs in original order. Capture topology, inset lanes, expiry and line response are unchanged. Dense-star comparisons and indexed/full boundary-path equivalence cover the optimized queries; eight-second paired state hashes are retained.
