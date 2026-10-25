"""Burrow Patrol: unique weapon logic and device-independent held input."""
import math
from system_panic.model import normalized,unit
from system_panic.pak_api import WeaponBase
from .powerup import BurrowPatrolPowerup
from .projectile import PressureLine

class BurrowPatrolWeapon(WeaponBase):
    def init(self):
        self.art=self.load_asset("weapon_sheet.png")
        self.sound=self.load_asset("shot.ogg")
        self._remaining=0.
        self._target=None
        self._pressure=0.
        self._line=None

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
        if not control.fire:
            self._pressure=max(0.,self._pressure-dt*.7)
            return
        if self._remaining<=0:
            self._remaining=.35
            self.sound.play(volume=.3)
        direction=self.aim(world)
        candidates=[e for e in world.enemies if e.health>0 and e.pos.distance_to(world.player.pos)<=self.reach(world)]
        explicit=world.component("pilot").aim_direction(world) is not None
        if explicit or not world.prefs.aim_assist:
            candidates=[e for e in candidates if normalized(e.pos-world.player.pos).dot(direction)>.45]
        if not candidates:
            self._target=None
            self._pressure=max(0.,self._pressure-dt)
            self.show_line(world,world.player.pos+direction*self.reach(world),0.)
            return
        target=next((e for e in candidates if e.id==self._target),None) or min(candidates,key=lambda e:e.pos.distance_squared_to(world.player.pos))
        if self._target!=target.id: self._target,self._pressure=target.id,0.
        self._pressure+=dt*(.85+.08*world.powerups_collected)
        world.hit_enemy(target,(7+2*world.powerups_collected)*dt)
        if self._pressure>=1:
            world.hit_enemy(target,max(45,target.max_health*1.25))
            world.burst(target.pos,world.pak("weapon").color,16)
            self._pressure=0.
        self.show_line(world,target.pos,self._pressure)

    def reach(self,world):
        return min(300.,145.+18*world.powerups_collected)

    def show_line(self,world,end,pressure):
        if self._line is None or not self._line.alive:
            self._line=PressureLine(self)
            world.effects.append(self._line)
        self._line.start=world.player.pos.copy()
        self._line.end=end.copy()
        self._line.pressure=pressure
        self._line.remaining=.05

    def create_powerup(self,world,position):
        return BurrowPatrolPowerup(position,self.sprite(world),world.pak("weapon").color)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
