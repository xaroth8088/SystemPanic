"""Component-local weapon state; no host behavior registry or sibling imports."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, normalized, unit
from system_panic.pak_api import WeaponBase, ProjectileBase
from .powerup import Upgrade
from .readout import Readout


class Weapon(WeaponBase):
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
            travel=.12+target.pos.distance_to(world.player.pos)/540
            return normalized(target.pos+target.vel*min(.75,travel)-world.player.pos)
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
        self.cooldown=max(0.,self.cooldown-dt)
        if control.fire and self.cooldown<=0:
            direction=self.aim(world)
            count=2+min(2,world.powerups_collected//3)
            for repeat in range(count):
                shot=Echo(world.player.pos+direction*18,direction,self,.12+repeat*.7,world.powerups_collected,repeat)
                world.projectiles.append(shot)
            self.sound.play(volume=.23)
            self.cooldown=.38
        self.previous_fire=control.fire


class Echo(ProjectileBase):
    def __init__(self, position, direction, weapon, delay, upgrades, repeat):
        super().__init__(position,direction*540,4)
        self.weapon,self.delay,self.upgrades,self.repeat=weapon,delay,upgrades,repeat
        self.age,self.hit=0.,set()

    def update(self, world, dt):
        self.age+=dt
        if self.age<self.delay:return
        previous=self.pos.copy()
        self.pos+=self.vel*dt
        if self.age>self.delay+2 or not(-10<self.pos.x<WIDTH+10 and -10<self.pos.y<HEIGHT+10):self.alive=False
        for wall in world.geometry:
            if wall.health>0 and wall.blocks_projectile(self) and wall.overlaps_segment(previous,self.pos):
                world.hit_cover(wall,24+self.upgrades*4)
                self.alive=False
                return
        for enemy in world.enemies:
            if enemy.id not in self.hit and enemy.pos.distance_to(self.pos)<enemy.radius+5:
                world.hit_enemy(enemy,27+self.upgrades*6)
                self.hit.add(enemy.id)
                if self.repeat==0:self.alive=False

    def draw(self, graphics, surface, world):
        color=(120,210,255) if self.repeat==0 else (175,150,255)
        if self.age<self.delay:
            pygame.draw.circle(surface,tuple(int(c*.5) for c in color),self.pos,7,1)
            pygame.draw.line(surface,color,self.pos,self.pos+self.vel*.022,1)
        else:
            image=graphics.render_sprite(self.weapon.sprite(world),22,color)
            surface.blit(image,image.get_rect(center=self.pos))
            pygame.draw.line(surface,color,self.pos-self.vel*.025,self.pos,2)
