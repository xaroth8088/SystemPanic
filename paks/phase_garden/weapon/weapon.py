"""PhaseGarden: Pak-owned trigger cadence and weapon behavior."""
from system_panic.model import Vec
from system_panic.model import normalized, unit
from system_panic.pak_api import WeaponBase
from .powerup import PhaseGardenPowerup
from .arc import ChainArc
from .readout import Readout


class PhaseGardenWeapon(WeaponBase):
    def init(self):
        self.pickup_sound = self.load_asset("pickup.ogg")
        self.projectiles = self.load_asset('weapon_sheet.png')
        self.shot_sound = self.load_asset("shot.ogg")
        self._remaining = 0.
        self.firing=False
        self.linked=0

    def reach(self,world):return 190+min(120,world.powerups_collected*12)
    def link_reach(self,world):return 110+min(80,world.powerups_collected*8)

    def sprite(self, world, entity=None):
        return self.projectiles.frame(int((world.time if world else 0)*8)%4,columns=4)

    def update(self, world, dt, control):
        self.firing=control.fire
        self._remaining = max(0., self._remaining - dt)
        if control.fire and self._remaining <= 0:
            self._remaining = 0.58
            self.fire(world, self.aim(world))
        if not any(isinstance(s,Readout) and s.weapon is self for s in world.projectiles):world.projectiles.append(Readout(self))

    def demo_controls(self,world,controls):
        if world.enemies:
            target=min(world.enemies,key=lambda e:e.pos.distance_squared_to(world.player.pos))
            delta=target.pos-world.player.pos
            if delta.length()>self.reach(world)-35:
                controls.x=int(delta.x>15)-int(delta.x< -15)
                controls.y=int(delta.y>15)-int(delta.y< -15)
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
        remaining = [enemy for enemy in world.enemies if enemy.health > 0]
        start = world.player.pos.copy()
        self.linked=0
        explicit=world.component('pilot').aim_direction(world) is not None or not world.prefs.aim_assist
        for index in range(min(5, 2 + world.powerups_collected // 3)):
            reach=self.reach(world) if index==0 else self.link_reach(world)
            candidates=[enemy for enemy in remaining if enemy.pos.distance_to(start)<=reach]
            if index==0 and explicit:candidates=[e for e in candidates if normalized(e.pos-start).dot(direction)>.5]
            if not candidates:break
            target = min(candidates, key=lambda enemy: enemy.pos.distance_squared_to(start))
            world.effects.append(ChainArc(start,target.pos.copy(),self.projectiles))
            world.hit_enemy(target, 26 + 3 * world.powerups_collected)
            self.linked+=1
            start = target.pos.copy()
            remaining.remove(target)
        if not self.linked:world.effects.append(ChainArc(start,start+direction*self.reach(world),self.projectiles))
        for wall in world.geometry:
            if wall.blocks_projectile(None) and wall.overlaps_circle(world.player.pos,self.reach(world)):
                world.hit_cover(wall, 15)

    def create_powerup(self,world,position):
        return PhaseGardenPowerup(position,self.projectiles,world.pak("weapon").color, self.pickup_sound)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
