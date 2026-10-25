"""PhaseGarden: Pak-owned trigger cadence and weapon behavior."""
from system_panic.model import circle_rect
from system_panic.model import normalized, unit
from system_panic.pak_api import WeaponBase
from .powerup import PhaseGardenPowerup
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
        remaining = [enemy for enemy in world.enemies if enemy.health > 0]
        start = world.player.pos.copy()
        for _ in range(min(5, 2 + world.powerups_collected // 3)):
            if not remaining:
                break
            target = min(remaining, key=lambda enemy: enemy.pos.distance_squared_to(start))
            world.effects.append(ChainArc(start, target.pos.copy()))
            world.hit_enemy(target, 26 + 3 * world.powerups_collected)
            start = target.pos.copy()
            remaining.remove(target)
        for wall in world.geometry:
            if circle_rect(world.player.pos, 150, wall.rect):
                world.hit_cover(wall, 15)

    def create_powerup(self,world,position):
        return PhaseGardenPowerup(position,self.sprite(world),world.pak("weapon").color)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
