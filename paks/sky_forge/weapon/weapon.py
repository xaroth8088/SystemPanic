"""SkyForge: Pak-owned trigger cadence and weapon behavior."""
from system_panic.pak_api import WeaponBase
from .projectile import Bomb


class SkyForgeWeapon(WeaponBase):
    def init(self):
        self.projectiles = self.load_asset('weapon_sheet.png')
        self.shot_sound = self.load_asset("shot.ogg")
        self._remaining = 0.

    def sprite(self, world, entity=None):
        return self.projectiles

    def update(self, world, dt, control):
        self._remaining = max(0., self._remaining - dt)
        if control.fire and self._remaining <= 0:
            self._remaining = 0.6
            self.fire(world, world.aim())

    def fire(self, world, direction):
        self.shot_sound.play(volume=.3)
        world.projectiles.append(Bomb(world, self, direction))
