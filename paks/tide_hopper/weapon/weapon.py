"""Tide Hopper: unique weapon logic and device-independent held input."""
import math
from system_panic.model import normalized,unit
from system_panic.pak_api import WeaponBase
from .powerup import TideHopperPowerup
from .projectile import Harpoon

class TideHopperWeapon(WeaponBase):
    def init(self):
        self.pickup_sound = self.load_asset("pickup.ogg")
        self.art=self.load_asset("weapon_sheet.png")
        self.sound=self.load_asset("shot.ogg")
        self._remaining=0.
        self._hook=None
        self.fire_held=False

    def on_level_start(self,world):
        self._hook=None
        self.fire_held=False

    def deactivate(self,world):
        if self._hook is not None:self._hook.alive=False
        self._hook=None

    def sprite(self,world,entity=None): return self.art.frame(int((world.time if world else 0)*8)%4,columns=4)

    def aim(self,world):
        intent=world.component("pilot").aim_direction(world)
        if intent is not None: return normalized(intent)
        targets=[enemy for enemy in world.enemies if enemy.health>0]
        if world.prefs.aim_assist and targets:
            target=min(targets,key=lambda e:e.pos.distance_squared_to(world.player.pos))
            return normalized(target.pos-world.player.pos)
        return unit(world.player.angle)

    def update(self,world,dt,control):
        self.fire_held=control.fire
        if self._hook is not None and (not self._hook.alive or self._hook not in world.projectiles): self._hook=None
        if control.fire and self._hook is None:
            self.sound.play(volume=.4)
            self._hook=Harpoon(world,self,self.aim(world))
            world.projectiles.append(self._hook)

    def throw_direction(self,world,target):
        intent=world.component('pilot').aim_direction(world)
        if intent is not None:return normalized(intent)
        others=[e for e in world.enemies if e.health>0 and e is not target]
        if world.prefs.aim_assist and others:
            other=min(others,key=lambda e:e.pos.distance_squared_to(target.pos))
            return normalized(other.pos-target.pos)
        return unit(world.player.angle)

    def demo_controls(self,world,controls):
        hook=self._hook
        if hook is not None and hook.target is not None and not hook.flung:
            others=[e for e in world.enemies if e.health>0 and e is not hook.target]
            controls.fire=not (hook.tension>.3 and any(e.pos.distance_to(hook.target.pos)<240 for e in others))
        return controls

    def create_powerup(self,world,position):
        return TideHopperPowerup(position,self.art,world.pak("weapon").color, self.pickup_sound)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
