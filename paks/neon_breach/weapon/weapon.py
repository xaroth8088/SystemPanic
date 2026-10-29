"""Neon Breach: unique weapon logic and device-independent held input."""
import math
from system_panic.model import normalized,unit
from system_panic.pak_api import WeaponBase
from .powerup import NeonBreachPowerup
from .projectile import PlasmaBall

class NeonBreachWeapon(WeaponBase):
    def init(self):
        self.pickup_sound = self.load_asset("pickup.ogg")
        self.art=self.load_asset("weapon_sheet.png")
        self.sound=self.load_asset("shot.ogg")
        self._remaining=0.
        self._shots=[]
        self.returns=0

    def on_level_start(self,world):
        self._shots.clear()
        self._remaining=0.

    def deactivate(self,world):
        for shot in self._shots:shot.alive=False
        self._shots.clear()

    def sprite(self,world,entity=None): return self.art.frame(int((world.time if world else 0)*8)%4,columns=4)

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
        self._shots=[s for s in self._shots if s.alive and s in world.projectiles]
        if control.fire and len(self._shots)<2+min(3,world.powerups_collected//2) and self._remaining<=0:
            self._remaining=.65
            self.sound.play(volume=.4)
            ball=PlasmaBall(world,self,self.aim(world))
            self._shots.append(ball)
            world.projectiles.append(ball)

    def demo_controls(self,world,controls):
        # Intercept our next perimeter return using the same left/right input
        # as a human. No pilot internals or ball state are changed by QA.
        candidates=[]
        for ball in self._shots:
            if not ball.alive:continue
            times=[(edge-ball.pos[axis])/ball.vel[axis] for axis,edge in ((0,24),(0,936),(1,24),(1,456)) if abs(ball.vel[axis])>1]
            times=[t for t in times if t>0]
            if times:candidates.append((min(times),ball))
        if candidates:
            time,ball=min(candidates,key=lambda item:item[0])
            point=ball.pos+ball.vel*time
            def perimeter(p):
                sides=(p.y,960-p.x,480-p.y,p.x)
                side=min(range(4),key=lambda i:sides[i])
                return (p.x-24,912+p.y-24,1344+936-p.x,2256+456-p.y)[side]
            error=(perimeter(point)-perimeter(world.player.pos)+1344)%2688-1344
            controls.x=0 if abs(error)<12 else 1 if error>0 else -1
            controls.special=abs(error)>180 and time<.8
        return controls

    def create_powerup(self,world,position):
        return NeonBreachPowerup(position,self.art,world.pak("weapon").color, self.pickup_sound)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
