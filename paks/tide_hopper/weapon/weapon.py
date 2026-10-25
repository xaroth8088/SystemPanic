"""Tide Hopper: unique weapon logic and device-independent held input."""
import math
from system_panic.model import normalized,unit
from system_panic.pak_api import WeaponBase
from .powerup import TideHopperPowerup
from .projectile import Harpoon

class TideHopperWeapon(WeaponBase):
    def init(self):
        self.art=self.load_asset("weapon_sheet.png")
        self.sound=self.load_asset("shot.ogg")
        self._remaining=0.
        self._hook=None

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
        if self._hook is not None and (not self._hook.alive or self._hook not in world.projectiles): self._hook=None
        if control.fire and self._hook is None:
            self.sound.play(volume=.4)
            self._hook=Harpoon(world,self,self.aim(world))
            world.projectiles.append(self._hook)

    def create_powerup(self,world,position):
        return TideHopperPowerup(position,self.sprite(world),world.pak("weapon").color)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
