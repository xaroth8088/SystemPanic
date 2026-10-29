"""VoidDrifter: Pak-owned trigger cadence and weapon behavior."""
from system_panic.model import normalized, unit
from system_panic.pak_api import WeaponBase
from .powerup import VoidDrifterPowerup
from .projectile import Lance
from .readout import Readout


class VoidDrifterWeapon(WeaponBase):
    def init(self):
        self.pickup_sound = self.load_asset("pickup.ogg")
        self.projectiles = self.load_asset('weapon_sheet.png')
        self.shot_sound = self.load_asset("shot.ogg")
        self._remaining = 0.
        self.charge=0.
        self._previous_fire=False

    def on_level_start(self,world):
        self.charge,self._remaining,self._previous_fire=0.,0.,False

    def on_shuffle(self,world,changed):
        self.charge,self._previous_fire=0.,False

    def sprite(self, world, entity=None):
        return self.projectiles.frame(int((world.time if world else 0)*8)%4,columns=4)

    def update(self, world, dt, control):
        self._remaining = max(0., self._remaining - dt)
        if control.fire and self._remaining<=0:
            self.charge=min(1.15,self.charge+dt)
        elif not control.fire and self._previous_fire:
            if self.charge+1e-8>=.18 and self._remaining<=0:
                self._remaining=.22
                self.fire(world,self.aim(world))
            self.charge=0.
        self._previous_fire=control.fire
        if not any(isinstance(s,Readout) and s.weapon is self for s in world.projectiles):world.projectiles.append(Readout(self))

    def demo_controls(self,world,controls):
        controls.fire=world.time%1.65<1.12
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
        charge=self.charge if self.charge>0 else 1.15
        world.projectiles.append(Lance(world,self,direction,charge))
        strength=max(0.,min(1.,(charge-.18)/.97))
        world.player.vel-=direction*(25+90*strength)

    def create_powerup(self,world,position):
        return VoidDrifterPowerup(position,self.projectiles,world.pak("weapon").color, self.pickup_sound)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
