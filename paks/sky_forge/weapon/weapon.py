"""Tap for an overhead sweep; charge a throw and physically recover the sword."""
from system_panic.model import Vec,normalized,unit,Cover
from system_panic.pak_api import WeaponBase
from .powerup import SkyForgePowerup
from .projectile import Swing,Sword
from .readout import Readout

class SkyForgeWeapon(WeaponBase):
    def init(self):
        self.pickup_sound=self.load_asset('pickup.ogg')
        self.projectiles=self.load_asset('weapon_sheet.png')
        self.shot_sound=self.load_asset('shot.ogg')
        self.throw_sound=self.load_asset('throw.ogg')
        self.charge=self._remaining=0.
        self._previous_fire=False
        self._sword=None
        self._demo_drop_direction=0
        self._demo_drop_top=0.
    def sprite(self,world,entity=None):return self.projectiles.frame(int((world.time if world else 0)*8)%4,columns=4)
    def on_level_start(self,world):
        self._demo_drop_direction=0
        self.charge=0.;self._previous_fire=False
        if self._sword is not None and self._sword.alive:
            self._sword.pos=world.safe_position(self._sword.pos,self._sword.radius,body=self._sword)
            self._sword.state='resting';self._sword.vel=Vec();self._sword.pickup_lock=.2
    def on_shuffle(self,world,changed):
        self.charge=0.;self._previous_fire=False
        if 'obstacles' in changed and self._sword is not None and self._sword.alive:
            self._sword.pos=world.safe_position(self._sword.pos,self._sword.radius,body=self._sword)
            self._sword.drop()
    def deactivate(self,world):
        if self._sword is not None:self._sword.alive=False
        self._sword=None
    def update(self,world,dt,control):
        self._remaining=max(0.,self._remaining-dt)
        if self._sword is not None and self._sword.alive:
            if self._sword not in world.projectiles:world.projectiles.append(self._sword)
            self.charge=0.
        elif control.fire and self._remaining<=0:self.charge=min(1.3,self.charge+dt)
        elif not control.fire and self._previous_fire:
            if self.charge>0 and self._remaining<=0:
                self.fire(world,self.aim(world),self.charge)
            self.charge=0.
        self._previous_fire=control.fire
        if not any(isinstance(s,Readout) and s.weapon is self for s in world.projectiles):world.projectiles.append(Readout(self))
    def fire(self,world,direction,charge=.1):
        if self._sword is not None and self._sword.alive:return
        self._remaining=.28
        if charge<.55:
            self.shot_sound.play(volume=.35)
            world.projectiles.append(Swing(world,self,direction))
        else:
            self.throw_sound.play(volume=.4)
            self._sword=Sword(world,self,direction,max(0.,min(1.,(charge-.55)/.75)))
            world.projectiles.append(self._sword)
    def reclaim(self,sword):
        if self._sword is sword:
            self._demo_drop_direction=0
            self._sword=None;self.pickup_sound.play(volume=.35)
    def aim(self,world):
        intent=world.component('pilot').aim_direction(world)
        if intent is not None:return normalized(intent)
        targets=[e for e in world.enemies if e.health>0]
        if world.prefs.aim_assist and targets:
            target=min(targets,key=lambda e:e.pos.distance_squared_to(world.player.pos))
            return normalized(target.pos-world.player.pos)
        return unit(world.player.angle)
    def demo_controls(self,world,controls):
        if self._sword is not None and self._sword.alive:
            target=self._sword.pos;delta=target-world.player.pos
            controls.fire=False
            if self._demo_drop_direction and world.player.pos.y<=self._demo_drop_top+world.player.radius+8:
                controls.x=self._demo_drop_direction;controls.y=0;controls.special=False
                return controls
            self._demo_drop_direction=0
            if delta.y>40:
                supports=[s for s in world.geometry if type(s) is Cover and s.health>0 and s.blocks_body(world.player) and abs(world.player.pos.y+world.player.radius-s.rect.top)<3 and s.rect.left-world.player.radius<world.player.pos.x<s.rect.right+world.player.radius]
                if supports:
                    deck=max(supports,key=lambda s:s.rect.top)
                    edge=min((deck.rect.left-world.player.radius-12,deck.rect.right+world.player.radius+12),key=lambda x:abs(x-world.player.pos.x))
                    self._demo_drop_direction=1 if edge>world.player.pos.x else -1
                    self._demo_drop_top=deck.rect.top
                    controls.x=self._demo_drop_direction;controls.y=0;controls.special=False
                    return controls
            desired=target.x
            overhead=[w for w in world.geometry if type(w) is Cover and w.health>0 and w.blocks_body(world.player) and w.rect.width>w.rect.height*2 and w.rect.bottom<world.player.pos.y-world.player.radius+4 and w.rect.top>target.y-20 and w.rect.left-world.player.radius<world.player.pos.x<w.rect.right+world.player.radius]
            if delta.y< -25 and overhead:
                deck=max(overhead,key=lambda w:w.rect.bottom)
                desired=min((deck.rect.left-world.player.radius-12,deck.rect.right+world.player.radius+12),key=lambda x:abs(x-world.player.pos.x))
            controls.x=int(desired-world.player.pos.x>12)-int(desired-world.player.pos.x< -12)
            controls.y=-1 if delta.y< -25 and world.time%1.1<.12 else 0
            controls.special=delta.y< -80 and world.time%2.8<.12
        else:
            close=any(e.health>0 and e.pos.distance_to(world.player.pos)<85 for e in world.enemies)
            controls.fire=world.time%(.5 if close else 1.15)<(.12 if close else .75)
        return controls
    def create_powerup(self,world,position):return SkyForgePowerup(position,self.projectiles,world.pak('weapon').color,self.pickup_sound)
    def on_powerup(self,world,count):world.burst(world.player.pos,world.pak('weapon').color,12)
