"""OrbitKeeper: Pak-owned trigger cadence and weapon behavior."""
from system_panic.pak_api import WeaponBase
from .projectile import Glaive


class OrbitKeeperWeapon(WeaponBase):
    def init(self):
        self.projectiles = self.load_asset('weapon_sheet.png')
        self.shot_sound = self.load_asset("shot.ogg")
        self._remaining = 0.

    def sprite(self, world, entity=None):
        return self.projectiles

    def update(self, world, dt, control):
        self._remaining = max(0., self._remaining - dt)
        if control.fire and self._remaining <= 0:
            self._remaining = 0.48
            self.fire(world, world.aim())

    def fire(self, world, direction):
        self.shot_sound.play(volume=.3)
        world.projectiles.append(Glaive(world, self, direction))
