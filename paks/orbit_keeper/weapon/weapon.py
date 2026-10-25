"""OrbitKeeper: Pak-owned trigger cadence and weapon behavior."""
from system_panic.model import normalized, unit
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
            self.fire(world, self.aim(world))

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
        world.projectiles.append(Glaive(world, self, direction))
