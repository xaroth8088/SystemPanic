"""OrbitKeeper: Pak-owned trigger cadence and weapon behavior."""
from system_panic.model import normalized, unit
from system_panic.pak_api import WeaponBase
from .powerup import OrbitKeeperPowerup
from .projectile import Glaive
from .readout import Readout


class OrbitKeeperWeapon(WeaponBase):
    def init(self):
        self.pickup_sound = self.load_asset("pickup.ogg")
        self.projectiles = self.load_asset('weapon_sheet.png')
        self.shot_sound = self.load_asset("shot.ogg")
        self._remaining = 0.
        self._active=[]
        self.fire_held=False
        self._held_for=self.catch_window=self.catch_flash=0.
        self.next_boost=1.

    def capacity(self,world):return 2+min(3,world.powerups_collected//3)

    def on_level_start(self,world):
        self._active.clear()
        self._remaining=self._held_for=self.catch_window=self.catch_flash=0.
        self.fire_held,self.next_boost=False,1.

    def deactivate(self,world):
        for shot in self._active:shot.alive=False
        self._active.clear()

    def caught(self,world):
        if not self.fire_held and self.catch_window>0:
            self.next_boost=1.8
            self.catch_flash=.35
            world.player.invulnerable=max(world.player.invulnerable,.15)
            self.shot_sound.play(volume=.12)

    def sprite(self, world, entity=None):
        return self.projectiles.frame(int((world.time if world else 0)*8)%4,columns=4)

    def update(self, world, dt, control):
        self._remaining = max(0., self._remaining - dt)
        self.catch_window=max(0.,self.catch_window-dt)
        self.catch_flash=max(0.,self.catch_flash-dt)
        self._active=[s for s in self._active if s.alive and s in world.projectiles]
        if control.fire:self._held_for+=dt
        elif self.fire_held:
            if self._held_for>=.35:self.catch_window=.22
            self._held_for=0.
        self.fire_held=control.fire
        if control.fire and self._remaining <= 0 and len(self._active)<self.capacity(world):
            self._remaining = 0.48
            self.fire(world, self.aim(world))
        if not any(isinstance(s,Readout) and s.weapon is self for s in world.projectiles):world.projectiles.append(Readout(self))

    def demo_controls(self,world,controls):
        incoming=any(s.alive and s.returning and s.pos.distance_to(world.player.pos)<90 for s in self._active)
        controls.fire=not incoming
        return controls

    def aim(self, world):
        intent = world.component("pilot").aim_direction(world)
        if intent is not None:
            return normalized(intent)
        targets = [enemy for enemy in world.enemies if enemy.health > 0]
        if world.prefs.aim_assist and targets:
            target = min(targets, key=lambda e: e.pos.distance_squared_to(world.player.pos))
            return normalized(target.pos - world.player.pos)
        return unit(world.player.angle)

    def fire(self, world, direction):
        if len([s for s in self._active if s.alive and s in world.projectiles])>=self.capacity(world):return
        self.shot_sound.play(volume=.3)
        shot=Glaive(world,self,direction,self.next_boost)
        self.next_boost=1.
        self._active.append(shot)
        world.projectiles.append(shot)

    def create_powerup(self,world,position):
        return OrbitKeeperPowerup(position,self.projectiles,world.pak("weapon").color, self.pickup_sound)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
