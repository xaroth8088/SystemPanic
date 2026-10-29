# Star Bastion

Read [Pak contracts](../AGENTS.md). Complete API 4 Pak with endless +1 initial enemy progression and six independently copyable role folders. No other Pak imports or host feature traits.

Align your bottom-lane fighter, fire salvos and reload between formation volleys.

Weapon: Battery 4+min(4,floor(n/2)) cells. Salvos cost one cell every .32s; empty reload 1.35s. Release with cells remaining for .48s to refill early. Damage 23+4n, 2+min(4,floor(n/3)) bolts. Assistance/guidance stays in a narrow .94-dot forward cone. Bolts expire at screen edges, never wrap.

Opposition: Formation armor x.5, dive exposure x1.6, return x1.25. When the attack timer expires it shoots immediately, with no tell/marker state. From level four it also commits to a 1.15s dive, followed by recovery/formation return. No replacement boss waves.

Four-frame pilot/enemy/weapon/terrain rows and an animated collectible use the original source `assets/images/star_bastion-renewal-source.png`. The local scenery, music and effects are installed; exact prompts, source hashes, measured extraction and mastering operations are in the asset ledgers. Generation is development-only.

Read [renewal verification](../../docs/pak-renewal.json) for the current tested checkpoint and limits. QA uses ordinary digital Controls, with no health, resource or damage grants.
