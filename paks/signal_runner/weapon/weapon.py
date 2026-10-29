"""SignalRunner: Pak-owned trigger cadence and weapon behavior."""
from system_panic.model import normalized, unit
from system_panic.pak_api import WeaponBase
from .powerup import SignalRunnerPowerup
from .projectile import Pulse


class SignalRunnerWeapon(WeaponBase):
    def init(self):
        self.pickup_sound = self.load_asset("pickup.ogg")
        self.projectiles = self.load_asset('weapon_sheet.png')
        self.shot_sound = self.load_asset("shot.ogg")
        self._remaining = 0.
        self.heat = 0.
        self.locked = False

    def capacity(self,world):
        return 1.+min(.6,world.powerups_collected*.05)

    def on_level_start(self,world):
        self.heat,self.locked,self._remaining=0.,False,0.

    def sprite(self, world, entity=None):
        return self.projectiles.frame(int((world.time if world else 0)*8)%4,columns=4)

    def update(self, world, dt, control):
        self._remaining = max(0., self._remaining - dt)
        self.heat=max(0.,self.heat-dt*(.18 if control.fire else 1.1))
        if self.locked and self.heat<=self.capacity(world)*.18:self.locked=False
        if control.fire and not self.locked and self._remaining <= 0:
            self._remaining = max(.07, .14 / (1 + .035 * world.powerups_collected))
            self.fire(world, self.aim(world))
            self.heat+=.18
            if self.heat>=self.capacity(world):self.locked=True

    def demo_controls(self,world,controls):
        controls.fire=world.time%1.15<.52
        controls.x=int(controls.x>.2)-int(controls.x<-.2)
        controls.y=int(controls.y>.2)-int(controls.y<-.2)
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
        self.shot_sound.play(volume=.3)
        world.projectiles.append(Pulse(world, self, direction))

    def create_powerup(self,world,position):
        return SignalRunnerPowerup(position,self.projectiles,world.pak("weapon").color, self.pickup_sound)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
