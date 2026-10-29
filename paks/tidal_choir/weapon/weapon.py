"""Component-local weapon state; no host behavior registry or sibling imports."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, normalized, unit
from system_panic.pak_api import WeaponBase, ProjectileBase
from .powerup import Upgrade
from .readout import Readout


class Weapon(WeaponBase):
    MIN_CHARGE = .6
    POWER_RADIUS = 30.

    def init(self):
        self.pickup_sound = self.load_asset("pickup.ogg")
        self.art = self.load_asset('weapon_sheet.png')
        self.sound = self.load_asset('shot.ogg')
        self.previous_fire = False
        self.charge = 0.
        self.cooldown = 0.
        self.heat = 0.
        self.locked = False
        self.active = []

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0) * 10) % 4, columns=4)

    def aim(self, world):
        intent = world.component('pilot').aim_direction(world)
        if intent is not None: return normalized(intent)
        targets = [e for e in world.enemies if e.health > 0]
        if world.prefs.aim_assist and targets:
            target = min(targets, key=lambda e: e.pos.distance_squared_to(world.player.pos))
            return normalized(target.pos - world.player.pos)
        return unit(world.player.angle)

    def create_powerup(self, world, position):
        return Upgrade(position, self.art, world.pak('weapon').color, self.pickup_sound)

    def on_powerup(self, world, count):
        world.burst(world.player.pos, world.pak('weapon').color, 12)

    def on_level_start(self, world):
        self.active.clear()
        self.charge = self.cooldown = self.heat = 0.
        self.locked = self.previous_fire = False

    def deactivate(self, world):
        for shot in self.active: shot.alive = False
        self.active.clear()

    def prune(self, world):
        self.active = [s for s in self.active if s.alive and s in world.projectiles]

    def feedback(self, world):
        if not any(isinstance(s, Readout) and s.weapon is self for s in world.projectiles):
            world.projectiles.append(Readout(self))

    def update(self, world, dt, control):
        self.feedback(world)
        self.prune(world)
        self.charge=min(1.2,self.charge+dt) if control.fire else self.charge
        tether=next((s for s in self.active if not s.released),None)
        if control.fire and tether is None:
            tether=Bubble(world.player.pos,self,world.powerups_collected)
            self.active.append(tether);world.projectiles.append(tether)
        if tether and not control.fire:
            tether.release(world,self.aim(world),self.charge)
            self.sound.play(volume=.35 if tether.powered else .1)
            self.charge=0.
        self.previous_fire=control.fire

    def demo_controls(self, world, controls):
        controls.fire=world.time%1.9<1.15
        return controls


class Bubble(ProjectileBase):
    def __init__(self, position, weapon, upgrades):
        super().__init__(position,Vec(),10)
        self.weapon,self.upgrades,self.released=weapon,upgrades,False
        self.age,self.charge,self.popped,self.hit=0.,0.,False,set()
        self.powered=False

    def release(self, world, direction, charge):
        self.released,self.age,self.charge=True,0.,charge
        self.vel=direction*235+world.player.vel*.25
        self.radius=12+30*charge
        self.powered=self.radius+1e-7>=Weapon.POWER_RADIUS

    def update(self, world, dt):
        self.age+=dt
        if not self.released:
            self.pos=world.player.pos+self.weapon.aim(world)*(24+self.weapon.charge*10)
            self.radius=12+self.weapon.charge*30
            return
        if not self.popped:
            self.vel.y-=75*dt
            self.pos+=self.vel*dt
            bounced=False
            for axis,limit in ((0,WIDTH),(1,HEIGHT)):
                if self.pos[axis]<self.radius:
                    self.pos[axis]=self.radius
                    if self.vel[axis]<0:
                        self.vel[axis]*=-1
                        bounced=True
                elif self.pos[axis]>limit-self.radius:
                    self.pos[axis]=limit-self.radius
                    if self.vel[axis]>0:
                        self.vel[axis]*=-1
                        bounced=True
            if bounced:self.vel*=.65
            for enemy in world.enemies:
                delta=self.pos-enemy.pos
                if self.powered and enemy.health>0 and delta.length()<self.radius+65:
                    world.move_body(enemy,normalized(delta)*min(120*dt,delta.length()),enemy.radius)
            if self.age>(1.35 if self.powered else .65):
                self.popped=True
                self.age=0.
                if self.powered:self.radius+=75+25*self.charge+min(30,self.upgrades*3)
                self.weapon.sound.play(volume=.25 if self.powered else .08)
        if self.popped:
            for enemy in world.enemies:
                if self.powered and enemy.id not in self.hit and enemy.pos.distance_to(self.pos)<self.radius+enemy.radius:
                    world.hit_enemy(enemy,37+50*self.charge+self.upgrades*10)
                    self.hit.add(enemy.id)
            if self.age>.28:self.alive=False

    def draw(self, graphics, surface, world):
        color=(130,240,230) if (self.powered or not self.released and self.weapon.charge>=Weapon.MIN_CHARGE) else (75,110,135)
        pygame.draw.circle(surface,color,self.pos,int(self.radius),2 if not self.popped else 3)
        if not self.popped:
            pygame.draw.circle(surface,(50,105,145),self.pos,int(self.radius+3),1)
            image=graphics.render_sprite(self.weapon.sprite(world),int(self.radius*1.6),color)
            surface.blit(image,image.get_rect(center=self.pos))
