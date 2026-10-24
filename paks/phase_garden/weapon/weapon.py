"""PhaseGarden: Pak-owned trigger cadence and weapon behavior."""
from system_panic.model import circle_rect
from system_panic.pak_api import WeaponBase
from .arc import ChainArc


class PhaseGardenWeapon(WeaponBase):
    def init(self):
        self.projectiles = self.load_asset('weapon_sheet.png')
        self.shot_sound = self.load_asset("shot.ogg")
        self._remaining = 0.

    def sprite(self, world, entity=None):
        return self.projectiles

    def update(self, world, dt, control):
        self._remaining = max(0., self._remaining - dt)
        if control.fire and self._remaining <= 0:
            self._remaining = 0.58
            self.fire(world, world.aim())

    def fire(self, world, direction):
        self.shot_sound.play(volume=.3)
        remaining = [enemy for enemy in world.enemies if enemy.health > 0]
        start = world.player.pos.copy()
        for _ in range(4):
            if not remaining:
                break
            target = min(remaining, key=lambda enemy: enemy.pos.distance_squared_to(start))
            world.effects.append(ChainArc(start, target.pos.copy()))
            world.hit_enemy(target, 26)
            start = target.pos.copy()
            remaining.remove(target)
        for wall in world.cover:
            if circle_rect(world.player.pos, 150, wall.rect):
                wall.health -= 15
