"""A short forward lunge; connecting knocks the pilot and target apart."""
from system_panic.model import Vec, normalized, unit, WIDTH, HEIGHT
from system_panic.pak_api import WeaponBase
from .powerup import MazeMuncherPowerup
from .projectile import BiteFlash


class MazeMuncherWeapon(WeaponBase):
    def init(self):
        self.pickup_sound = self.load_asset("pickup.ogg")
        self.art = self.load_asset("weapon_sheet.png")
        self.sound = self.load_asset("shot.ogg")
        self._remaining = 0.
        self._dash = 0.
        self._direction = Vec(1, 0)
        self.backbite_flash=0.

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0)*8)%4,columns=4)

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
        self.backbite_flash=max(0.,self.backbite_flash-dt)
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
        motion = self.move(world,p,self._direction * 460 * active)
        edge = self.delta(before,p.pos)
        hits = []
        for enemy in world.enemies:
            if enemy.health <= 0:
                continue
            t = max(0., min(1., self.delta(before,enemy.pos).dot(edge) / edge.length_squared())) if edge.length_squared() else 0.
            if self.delta(before + edge*t,enemy.pos).length() <= p.radius + enemy.radius + 2:
                hits.append((t, enemy))
        if hits:
            enemy = min(hits, key=lambda item: item[0])[1]
            direction = normalized(self.delta(p.pos,enemy.pos), self._direction)
            # Approach from behind a moving foe for a decisive backbite.
            rear=enemy.vel.length_squared()>4 and normalized(enemy.vel).dot(self._direction)>.4
            if rear:self.backbite_flash=.4
            world.hit_enemy(enemy, (20 + 5 * level)*(1.75 if rear else 1.))
            p.invulnerable=max(p.invulnerable,.22)
            self.move(world,enemy,direction * (42 + min(25, 3*level)))
            enemy.vel += direction * 220
            self.move(world,p,-direction * 28)
            p.vel = -direction * 160
            self._dash = 0.
        elif motion.normals:
            self._dash = 0.
        world.effects.append(BiteFlash(before, before+edge, world.pak("weapon").color))

    def delta(self,a,b):
        d=b-a
        if abs(d.x)>WIDTH/2:d.x-=WIDTH*(1 if d.x>0 else -1)
        return d

    def move(self,world,body,step):
        motion=world.move_body(body,step,body.radius,bounds=None)
        body.pos.x%=WIDTH
        body.pos.y=max(body.radius,min(HEIGHT-body.radius,body.pos.y))
        return motion

    def create_powerup(self,world,position):
        return MazeMuncherPowerup(position,self.art,world.pak("weapon").color, self.pickup_sound)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
