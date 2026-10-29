# Physical loom thread

One active hook travels at640px/s and must reach an enemy. Holding fire reels a latched body through world.move_body, deals19+2.5*upgrades DPS and ticks real span crossings. Release snaps the actual player/target span for tension-scaled damage. A short-distance or1.4s reel limit also snaps. Walls occlude hook flight and the held span. Hook lifetime3.2s, maximum distance660, all local.

A weapon swap/clear can remove scheduled objects; update prunes stale hook references before casting. No pilot movement/state is borrowed. Upgrade counts raise impact/reel/snap formulas. powerup.py captures raw art/chime and lasts50 active seconds; old drops survive provider swaps and chime only on successful collect_powerup.

Outbound wall contact dispatches world.hit_cover, so the ordinary harpoon really turns wind hubs. Snap checks the current line before damage because release dispatch follows pilot movement and precedes the next projectile update; newly occluding geometry cancels it. Both interactions have ordinary-input regression coverage.
