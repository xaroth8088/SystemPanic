"""Vector Coil: unique weapon logic and device-independent held input."""
import math
from system_panic.model import normalized,unit
from system_panic.pak_api import WeaponBase
from .projectile import PrismCross

class VectorCoilWeapon(WeaponBase):
    def init(self):
        self.art=self.load_asset("weapon_sheet.png")
        self.sound=self.load_asset("shot.ogg")
        self._remaining=0.
        self._beam=None

    def sprite(self,world,entity=None): return self.art

    def aim(self,world):
        intent=world.component("pilot").aim_direction(world)
        if intent is not None: return normalized(intent)
        targets=[enemy for enemy in world.enemies if enemy.health>0]
        if world.prefs.aim_assist and targets:
            target=min(targets,key=lambda e:e.pos.distance_squared_to(world.player.pos))
            return normalized(target.pos-world.player.pos)
        return unit(world.player.angle)

    def update(self,world,dt,control):
        self._remaining=max(0.,self._remaining-dt)
        if not control.fire: return
        direction=self.aim(world)
        base=math.atan2(direction.y,direction.x)+world.time*1.65
        origin=world.player.pos
        ends=[origin+unit(base+i*math.pi/2)*1000 for i in range(4)]
        for enemy in world.enemies:
            delta=enemy.pos-origin
            if any(0<delta.dot(normalized(end-origin))<1000 and abs(delta.cross(normalized(end-origin)))<enemy.radius+5 for end in ends):
                world.hit_enemy(enemy,220*dt)
        for wall in world.cover:
            if any(wall.rect.clipline(origin,end) for end in ends): wall.health-=65*dt
        if self._beam is None or not self._beam.alive:
            self._beam=PrismCross(self)
            world.effects.append(self._beam)
        self._beam.start=origin.copy()
        self._beam.ends=ends
        self._beam.remaining=.05
        if self._remaining<=0:
            self._remaining=.3
            self.sound.play(volume=.23)
