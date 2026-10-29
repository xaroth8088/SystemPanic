# Tide Hopper

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak with endless +1 initial enemy progression and six independently copyable role folders. No other Pak imports or host feature traits.

Hop between lanes, hook traffic, hold to reel, or release to fling it into a collision.

Weapon: One hook: 18+4n initial damage, 38+8n reel finish, reel factor 4+.4n. Tow calls move_body on the actual enemy and can damage blocking cover; prolonged blocking releases the hook. Release a held target to fling at 420+200*tension+20n. Body/obstacle impacts deal 32+8n+25*tension to the caught and struck enemy. Flight owns a hit set, fuse and cleanup; enemies remain original world entities and deaths count once.

Opposition: Traffic now hops between the same 24+48k centers as the pilot and pauses visibly between steps. Normal pilot hops span one cell; the protected ferry hop spans two (96px). Later traffic changes rows on this lattice. Public positional displacement from a foreign weapon cancels the current route and yields briefly; sustained harpoon towing is never snapped back. After release traffic travels to a clear node through collision checks. No sibling-private capture flag is read.

Four-frame pilot/enemy/weapon/terrain rows and an animated collectible use the original source `assets/images/tide_hopper-renewal-source.png`. The local scenery, music and effects are installed; exact prompts, source hashes, measured extraction and mastering operations are in the asset ledgers. Generation is development-only.

Read [renewal verification](../../docs/pak-renewal.json) for the current tested checkpoint and limits. QA uses ordinary digital Controls, with no health, resource or damage grants.

Facing refinement: the local pilot sheet is 4 columns × 4 animation poses, selected by this role with zero in-plane rotation or mirroring. Columns follow E/S/W/N. Original built-in imagegen source: assets/images/tide_hopper-facing-source.png. The exact input snapshot, prompts and measured lossless extraction are registered in the asset ledgers. Only supported movement facings were generated; controls and physics are unchanged by art selection.
