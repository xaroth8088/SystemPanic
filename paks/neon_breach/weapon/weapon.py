"""Neon Breach: unique weapon logic and device-independent held input."""
import math
from system_panic.model import normalized,unit
from system_panic.pak_api import WeaponBase
from .powerup import NeonBreachPowerup
from .projectile import PlasmaBall

class NeonBreachWeapon(WeaponBase):
    def init(self):
        self.art=self.load_asset("weapon_sheet.png")
        self.sound=self.load_asset("shot.ogg")
        self._remaining=0.
        self._shots=[]

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
        self._shots=[s for s in self._shots if s.alive and s in world.projectiles]
        if control.fire and len(self._shots)<2+min(3,world.powerups_collected//2) and self._remaining<=0:
            self._remaining=.65
            self.sound.play(volume=.4)
            ball=PlasmaBall(world,self,self.aim(world))
            self._shots.append(ball)
            world.projectiles.append(ball)

    def create_powerup(self,world,position):
        return NeonBreachPowerup(position,self.sprite(world),world.pak("weapon").color)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
