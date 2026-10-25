"""A short forward lunge; connecting knocks the pilot and target apart."""
from system_panic.model import Vec, normalized, unit
from system_panic.pak_api import WeaponBase
from .powerup import MazeMuncherPowerup
from .projectile import BiteFlash


class MazeMuncherWeapon(WeaponBase):
    def init(self):
        self.art = self.load_asset("weapon_sheet.png")
        self.sound = self.load_asset("shot.ogg")
        self._remaining = 0.
        self._dash = 0.
        self._direction = Vec(1, 0)

    def sprite(self, world, entity=None):
        return self.art

    def aim(self, world):
        intent = world.component("pilot").aim_direction(world)
        if intent is not None:
            return normalized(intent)
        # Forward means the pilot's facing, independent of automatic targeting.
        return unit(world.player.angle)

    def on_shuffle(self, world, changed):
        self._dash = 0.

    def on_level_start(self, world):
        self._dash = 0.

    def update(self, world, dt, control):
        self._remaining = max(0., self._remaining - dt)
        level = world.powerups_collected
        if control.fire and self._remaining <= 0 and self._dash <= 0:
            self._remaining = max(.3, .62 / (1 + .035 * level))
            self._dash = .14 + min(.08, level * .008)
            self._direction = self.aim(world)
            self.sound.play(volume=.35)
        if self._dash <= 0:
            return
        active = min(dt, self._dash)
        self._dash -= active
        p = world.player
        before = p.pos.copy()
        motion = world.move_body(p, self._direction * 460 * active, p.radius)
        edge = p.pos - before
        hits = []
        for enemy in world.enemies:
            if enemy.health <= 0:
                continue
            t = max(0., min(1., (enemy.pos-before).dot(edge) / edge.length_squared())) if edge.length_squared() else 0.
            if (before + edge*t).distance_to(enemy.pos) <= p.radius + enemy.radius + 2:
                hits.append((t, enemy))
        if hits:
            enemy = min(hits, key=lambda item: item[0])[1]
            direction = normalized(enemy.pos - p.pos, self._direction)
            world.hit_enemy(enemy, 20 + 5 * level)
            world.move_body(enemy, direction * (42 + min(25, 3*level)), enemy.radius)
            enemy.vel += direction * 220
            world.move_body(p, -direction * 28, p.radius)
            p.vel = -direction * 160
            self._dash = 0.
        elif motion.normals:
            self._dash = 0.
        world.effects.append(BiteFlash(before, p.pos, world.pak("weapon").color))

    def create_powerup(self,world,position):
        return MazeMuncherPowerup(position,self.sprite(world),world.pak("weapon").color)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
