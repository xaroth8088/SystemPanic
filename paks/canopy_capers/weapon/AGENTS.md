# Canopy automatic momentum stomp

There is no trigger gate. Whenever the pilot is physically descending (positive vertical speed), retain previous pilot position plus each enemy's previous position/top and detect a relative foot/top crossing with horizontal foot overlap. Require positive closing vertical speed. Choose the earliest physical crossing, never every nearby enemy. Pilot/enemy displacement above max(24,2*speed*dt+6) is a discontinuity and cannot create swept damage. Newly spawned/adopted bodies need one clean history sample. These guards reject both pilot and enemy teleport phantom hits.

Requested damage is .18 * (pilot.vel.y - enemy.vel.y) * (1+.16*world.powerups_collected) * (1+.08*(chain-1)). Thus twice the relative downward momentum gives twice the raw damage at equal upgrades/chain. Chains expire after2.8 active seconds and cap at6. Rebound is-(260+min(200,.3*impact_speed)+min(70,7*upgrades)); contact cooldown is.12s and pilot contact grace is.16s. Blocked/armored physical top contact still rebounds. Ascending or side contacts never stomp. The weapon does not give a foreign pilot jump or alter its ordinary locomotion.

Stomp flashes use captured local boot art and are visual-only effects. No fixed HUD meter, target cue or distant projectile damage substitute exists. powerup.py retains captured art/color/chime, attracts within155px, expires after50 active seconds and chimes only on successful collection. Persistent upgrade count is interpreted only by this weapon.

Focused tests verify automatic contact with fire released, exact54/108 damage for300/600px/s, relative enemy velocity, proportional upgrades, ascent/side misses, physical rebound, no duplicate crossing, both teleport guards and pickup count/expiry.
