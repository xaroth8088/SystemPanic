"""Star Bastion: unique weapon logic and device-independent held input."""
import math
from system_panic.model import normalized,unit
from system_panic.pak_api import WeaponBase
from .powerup import StarBastionPowerup
from .projectile import SalvoBolt

class StarBastionWeapon(WeaponBase):
    def init(self):
        self.pickup_sound = self.load_asset("pickup.ogg")
        self.art=self.load_asset("weapon_sheet.png")
        self.sound=self.load_asset("shot.ogg")
        self._remaining=0.
        self.cells=4
        self.reloading=0.
        self._release=0.

    def capacity(self,world):return 4+min(4,world.powerups_collected//2)

    def on_level_start(self,world):
        self.cells=self.capacity(world)
        self.reloading=self._remaining=self._release=0.

    def sprite(self,world,entity=None): return self.art.frame(int((world.time if world else 0)*8)%4,columns=4)

    def aim(self,world):
        intent=world.component("pilot").aim_direction(world)
        if intent is not None: return normalized(intent)
        targets=[enemy for enemy in world.enemies if enemy.health>0]
        if world.prefs.aim_assist and targets:
            facing=unit(world.player.angle)
            targets=[e for e in targets if normalized(e.pos-world.player.pos).dot(facing)>.94]
            if targets:
                target=min(targets,key=lambda e:e.pos.distance_squared_to(world.player.pos))
                return normalized(target.pos-world.player.pos)
        return unit(world.player.angle)

    def update(self,world,dt,control):
        self._remaining=max(0.,self._remaining-dt)
        self.reloading=max(0.,self.reloading-dt)
        self._release=0. if control.fire else self._release+dt
        if self.cells==0 and self.reloading==0:self.cells=self.capacity(world)
        # Releasing early performs a faster tactical reload. Holding through an
        # empty battery commits to the longer automatic reload.
        if self._release>=.48 and self.cells<self.capacity(world) and self.reloading==0:
            self.cells=self.capacity(world)
            self._release=0.
        if control.fire and not self.reloading and self._remaining<=0:
            self._remaining=.32
            self.cells-=1
            if self.cells==0:self.reloading=1.35
            direction=self.aim(world)
            guided=world.prefs.aim_assist and world.component("pilot").aim_direction(world) is None
            self.sound.play(volume=.3)
            count=2+min(4,world.powerups_collected//3)
            for side in (-9,9,0,-27,27,-45)[:count]: world.projectiles.append(SalvoBolt(world,self,direction,side,guided))

    def demo_controls(self,world,controls):
        controls.fire=world.time%1.5<.95
        return controls

    def create_powerup(self,world,position):
        return StarBastionPowerup(position,self.art,world.pak("weapon").color, self.pickup_sound)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
