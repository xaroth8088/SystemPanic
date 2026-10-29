"""Nectar-funded cultivation: the weapon owns wells, water and plant growth."""
import math
import random

import pygame
from system_panic.model import Cover, Vec, WIDTH, HEIGHT, normalized, unit
from system_panic.pak_api import WeaponBase, ProjectileBase
from .powerup import Upgrade
from .readout import Readout


class Weapon(WeaponBase):
    def init(self):
        self.pickup_sound = self.load_asset("pickup.ogg")
        self.art = self.load_asset('weapon_sheet.png')
        self.sound = self.load_asset('shot.ogg')
        self.previous_fire = self.locked = False
        self.charge = self.cooldown = self.heat = 0.
        self.water = 0.
        self.active, self.wells = [], []
        self.well_wave = -1
        self.refilling = False
        self.demo_refill = True
        self.demo_bloom_until = 0.

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0)*10)%4, columns=4)

    def aim(self, world):
        intent = world.component('pilot').aim_direction(world)
        if intent is not None:
            return normalized(intent)
        targets = [e for e in world.enemies if e.health > 0]
        if world.prefs.aim_assist and targets:
            return normalized(min(targets, key=lambda e: e.pos.distance_squared_to(world.player.pos)).pos-world.player.pos)
        return unit(world.player.angle)

    def capacity(self, world):
        return 4.+min(20, world.powerups_collected*2)

    def build_wells(self, world):
        rng = random.Random(f'{world.seed}:nectar:{world.wave}')
        # Cycle separated vertical bands while varying both coordinates. This
        # moves the refill routes each level without consuming combat RNG or
        # depending on which earlier levels happened to be visited.
        bands=((95,125),(225,255),(355,385))
        phase=(world.wave-1)%len(bands)
        self.wells=[]
        for index,(left,right) in enumerate(((95,410),(550,865))):
            low,high=bands[(phase+index)%len(bands)]
            position=world.safe_position(Vec(rng.uniform(left,right),rng.uniform(low,high)),44)
            self.wells.append(NectarWell(position,self))
        self.well_wave = world.wave
        world.set_geometry(self, self.wells)

    def near_well(self, world):
        return any(world.player.pos.distance_to(well.position) < 39 for well in self.wells)

    def in_well(self, world):
        return any(world.player.pos.distance_to(well.position)<=NectarWell.RADIUS+world.player.radius
                   for well in self.wells)

    def create_powerup(self, world, position):
        return Upgrade(position, self.art, world.pak('weapon').color, self.pickup_sound)

    def on_powerup(self, world, count):
        # Larger capacity is earned, but upgrading never creates free nectar.
        world.burst(world.player.pos, world.pak('weapon').color, 12)

    def on_level_start(self, world):
        self.active.clear()
        self.charge = self.cooldown = 0.
        self.previous_fire = False
        self.build_wells(world)

    def on_shuffle(self, world, changed):
        self.active.clear()
        self.previous_fire = False
        if 'obstacles' in changed:
            self.build_wells(world)

    def deactivate(self, world):
        for pod in self.active:
            pod.alive = False
        self.active.clear()
        world.clear_geometry(self)

    def prune(self, world):
        self.active = [s for s in self.active if s.alive and s in world.projectiles]

    def update(self, world, dt, control):
        if self.well_wave != world.wave:
            self.build_wells(world)
        self.prune(world)
        if not any(isinstance(s, Readout) and s.weapon is self for s in world.projectiles):
            world.projectiles.append(Readout(self))
        self.cooldown = max(0., self.cooldown-dt)
        self.refilling = (not control.fire and not control.x and not control.y and
                          world.player.vel.length_squared() < 25**2 and self.near_well(world))
        if self.refilling:
            self.water = min(self.capacity(world), self.water+2.*dt)
        if control.fire:
            if self.cooldown <= 0 and len(self.active) < 12 and not self.in_well(world):
                if not any(s.pos.distance_to(world.player.pos) < 34 for s in self.active):
                    pod = Pod(world.player.pos, self, 0)
                    self.active.append(pod)
                    world.projectiles.append(pod)
                self.cooldown = .3
            candidates = [s for s in self.active if not s.bloom and s.growth < 1 and
                          s.pos.distance_to(world.player.pos) < 95]
            if candidates and self.water > 0:
                pod = min(candidates, key=lambda s: s.pos.distance_squared_to(world.player.pos))
                used = min(self.water, .85*dt, 1.-pod.growth)
                self.water -= used
                pod.growth += used
                pod.watered = .12
        elif self.previous_fire:
            for index, pod in enumerate(self.active):
                pod.fuse = min(pod.fuse, index*.11)
        self.charge = self.water/self.capacity(world)*1.2
        self.previous_fire = control.fire

    def demo_controls(self, world, controls):
        if self.water < .05:
            self.demo_refill = True
        if self.demo_refill and self.wells:
            well = min(self.wells, key=lambda s: s.position.distance_squared_to(world.player.pos))
            delta = well.position-world.player.pos-world.player.vel*.15
            controls.x = float(delta.x > 12)-float(delta.x < -12)
            controls.y = float(delta.y > 12)-float(delta.y < -12)
            controls.fire = controls.special = False
            if self.near_well(world):
                controls.x = controls.y = 0
            if self.water >= self.capacity(world)-.05:
                self.demo_refill = False
            return controls
        if self.in_well(world):
            well=min(self.wells,key=lambda s:s.position.distance_squared_to(world.player.pos))
            direction=normalized(world.player.pos-well.position)
            controls.x=float(direction.x>.2)-float(direction.x<-.2)
            controls.y=float(direction.y>.2)-float(direction.y<-.2)
            controls.fire=controls.special=False
            return controls
        if world.time < self.demo_bloom_until:
            controls.fire = False
            return controls
        growing = [s for s in self.active if not s.bloom and s.pos.distance_to(world.player.pos) < 70]
        if growing:
            pod = max(growing, key=lambda s: s.growth)
            if pod.growth >= .95 or any(e.pos.distance_to(world.player.pos) < 55 for e in world.enemies):
                controls.fire = False
                self.demo_bloom_until = world.time+.65
            else:
                controls.x = controls.y = 0
                controls.fire, controls.special = True, False
        elif world.enemies:
            nearest = min(e.pos.distance_to(world.player.pos) for e in world.enemies)
            controls.fire = nearest < 230
        return controls


class NectarWell(Cover):
    RADIUS=42

    def __init__(self, position, weapon):
        self.position, self.weapon = Vec(position), weapon
        super().__init__(pygame.Rect(round(position.x-42),round(position.y-42),84,84),1.,1.)

    def blocks_body(self, body):
        return False

    def blocks_projectile(self, projectile):
        return False

    def damage(self, world, amount):
        return 0.

    def draw(self, graphics, surface, world):
        color = (115,205,180) if self.weapon.refilling and self.position.distance_to(world.player.pos)<39 else (75,130,110)
        pygame.draw.circle(surface,(23,55,48),self.position,39)
        pygame.draw.circle(surface,color,self.position,42,2)
        for index in range(4):
            point=self.position+unit(index*math.tau/4+world.time*.3)*27
            pygame.draw.circle(surface,(110,175,145),point,2)
        pass
        pass


class Pod(ProjectileBase):
    def __init__(self, position, weapon, upgrades=0):
        super().__init__(position,Vec(),9)
        self.weapon, self.age = weapon, 0.
        self.growth = self.watered = 0.
        self.fuse, self.bloom = 100., False
        self.hit = set()

    def update(self, world, dt):
        self.age += dt
        self.fuse -= dt
        self.watered = max(0., self.watered-dt)
        maturity = self.growth
        trigger = self.fuse <= 0 or (maturity >= 1 and any(e.health>0 and e.pos.distance_to(self.pos)<52 for e in world.enemies))
        if not self.bloom and (trigger or self.age>16):
            if maturity < .2 or self.age > 16:
                self.alive = False
                return
            self.bloom, self.fuse = True, .32
            self.radius, self.damage = 28+70*maturity, 8+112*maturity**2.4
            self.weapon.sound.play(volume=.27)
            for other in self.weapon.active:
                if other is not self and not other.bloom and other.growth >= .2 and other.pos.distance_to(self.pos)<self.radius+20:
                    other.fuse = min(other.fuse,.09)
        if self.bloom:
            for enemy in world.enemies:
                if enemy.id not in self.hit and enemy.pos.distance_to(self.pos)<self.radius+enemy.radius:
                    world.hit_enemy(enemy,self.damage)
                    self.hit.add(enemy.id)
            if self.fuse<=0:
                self.alive=False

    def is_threat_to(self, world, body):
        return body is not world.player and not self.bloom and self.growth>=.8

    def draw(self, graphics, surface, world):
        if self.bloom:
            pygame.draw.circle(surface,(247,143,185),self.pos,int(self.radius*(1-self.fuse/.4)),3)
        else:
            image=graphics.render_sprite(self.weapon.art.frame(min(3,int(self.growth*3)),columns=4),int(19+21*self.growth))
            surface.blit(image,image.get_rect(center=self.pos))
            pygame.draw.circle(surface,(94,150,90),self.pos,18+int(self.growth*10),1)
            if self.watered>0:
                pygame.draw.line(surface,(100,225,230),world.player.pos,self.pos,2)
