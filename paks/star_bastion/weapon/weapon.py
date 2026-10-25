"""Star Bastion: unique weapon logic and device-independent held input."""
import math
from system_panic.model import normalized,unit
from system_panic.pak_api import WeaponBase
from .powerup import StarBastionPowerup
from .projectile import SalvoBolt

class StarBastionWeapon(WeaponBase):
    def init(self):
        self.art=self.load_asset("weapon_sheet.png")
        self.sound=self.load_asset("shot.ogg")
        self._remaining=0.

    def sprite(self,world,entity=None): return self.art

    def aim(self,world):
        intent=world.component("pilot").aim_direction(world)
        if intent is not None: return normalized(intent)
        targets=[enemy for enemy in world.enemies if enemy.health>0]
        if world.prefs.aim_assist and targets:
            target=min(targets,key=lambda e:e.pos.distance_squared_to(world.player.pos))
            return normalized(target.pos-world.player.pos)
        return unit(world.player.angle)

    def update(self,world,dt,control):
        self._remaining=max(0.,self._remaining-dt)
        if control.fire and self._remaining<=0:
            self._remaining=.32
            direction=self.aim(world)
            guided=world.prefs.aim_assist and world.component("pilot").aim_direction(world) is None
            self.sound.play(volume=.3)
            count=2+min(4,world.powerups_collected//3)
            for side in (-9,9,0,-27,27,-45)[:count]: world.projectiles.append(SalvoBolt(world,self,direction,side,guided))

    def create_powerup(self,world,position):
        return StarBastionPowerup(position,self.sprite(world),world.pak("weapon").color)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
