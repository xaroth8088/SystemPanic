"""A molten-marble kiln: sustained fire builds pressure; release cools the nozzle."""
import math
import pygame
from system_panic.model import Vec, normalized, unit, WIDTH, HEIGHT
from system_panic.pak_api import WeaponBase, ProjectileBase
from .powerup import Upgrade


class Kiln(WeaponBase):
    def init(self):
        self.art = self.load_asset('weapon_sheet.png')
        self.sound = self.load_asset('shot.ogg')
        self.chime = self.load_asset('pickup.ogg')
        self.pressure = self.cooldown = self.locked = 0.
        self.display = None

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0)*9)%4, columns=4)

    def create_powerup(self, world, position):
        return Upgrade(position,self.art,(255,183,112),self.chime)

    def on_powerup(self, world, count):
        world.burst(world.player.pos,(255,199,137),12)

    def on_level_start(self, world):
        self.pressure = self.cooldown = self.locked = 0.
        self.display = None

    def deactivate(self, world):
        if self.display is not None:
            self.display.alive = False
        self.display = None

    def update(self, world, dt, control):
        self.cooldown = max(0.,self.cooldown-dt)
        self.locked = max(0.,self.locked-dt)
        if self.display is None or not self.display.alive or self.display not in world.projectiles:
            self.display = Nozzle(self)
            world.projectiles.append(self.display)
        if not control.fire or self.locked:
            self.pressure = max(0.,self.pressure-dt*.72)
            return
        self.pressure = min(1.,self.pressure+dt*.28)
        if self.cooldown > 0:
            return
        intent = world.component('pilot').aim_direction(world)
        targets = [e for e in world.enemies if e.health > 0]
        if intent is not None:
            heading = normalized(intent)
        elif world.prefs.aim_assist and targets:
            target = min(targets,key=lambda e:e.pos.distance_squared_to(world.player.pos))
            heading = normalized(target.pos+target.vel*.1-world.player.pos)
        else:
            heading = unit(world.player.angle)
        world.projectiles.append(Marble(world.player.pos+heading*15,heading,self.pressure,world.powerups_collected,self.art))
        self.sound.play(volume=.35+self.pressure*.15)
        self.cooldown = .34-self.pressure*.09
        if self.pressure >= .995:
            self.locked = .9
            world.burst(world.player.pos,(226,235,233),8)

    def demo_controls(self, world, controls):
        controls.fire = world.time % 3.2 < 2.65
        return controls


class Nozzle(ProjectileBase):
    def __init__(self, weapon):
        super().__init__(Vec(),Vec(),1)
        self.weapon = weapon

    def update(self, world, dt):
        self.pos = world.player.pos.copy()

    def draw(self, graphics, surface, world):
        if self.weapon.pressure < .05 and not self.weapon.locked:
            return
        p = world.player
        color = (156,219,231) if self.weapon.locked else (255,145+int(80*(1-self.weapon.pressure)),97)
        # Four on-body heat pips make pressure legible with foreign pilots.
        for index in range(4):
            if self.weapon.locked or self.weapon.pressure > index*.25:
                position = p.pos + Vec((index-1.5)*5, p.radius+7)
                pygame.draw.circle(surface,color,position,2)


class Marble(ProjectileBase):
    def __init__(self, position, heading, pressure, upgrades, art):
        super().__init__(position,heading*(320+pressure*170),7+pressure*2)
        self.art = art
        self.heat = .5+pressure*.5
        self.damage = 21+pressure*23+upgrades*3
        self.age = 0.
        self.bounces = 1+int(pressure*3)+min(3,upgrades//2)
        self.hit = set()

    def update(self, world, dt):
        self.age += dt
        self.heat = max(0.,self.heat-dt*.25)
        if self.age > 4.2:
            self.shatter(world)
            return
        # Small steps preserve the exact obstacle hit even at full pressure.
        steps = max(1,math.ceil(self.vel.length()*dt/4))
        for _ in range(steps):
            old = self.pos.copy()
            movement = self.vel*(dt/steps)
            normals = []
            contacted = set()
            for axis in (0, 1):
                self.pos[axis] += movement[axis]
                normal = Vec()
                normal[axis] = -1 if movement[axis] > 0 else 1
                walls = [wall for wall in world.geometry if wall.health > 0 and wall.blocks_projectile(self)
                         and wall.overlaps_circle(self.pos, self.radius)]
                outside = self.pos[axis] < self.radius or self.pos[axis] > (WIDTH if axis == 0 else HEIGHT)-self.radius
                if walls or outside:
                    self.pos[axis] -= movement[axis]
                    if movement[axis]:
                        normals.append(normal)
                    for wall in walls:
                        if id(wall) not in contacted:
                            world.hit_cover(wall,self.damage*(.5+self.heat*.5))
                            contacted.add(id(wall))
            if normals:
                if self.bounces <= 0 or self.heat <= .08:
                    self.shatter(world)
                    return
                self.bounces -= 1
                for normal in normals:
                    if self.vel.dot(normal) < 0:
                        self.vel -= normal*2*self.vel.dot(normal)
                self.heat = max(0.,self.heat-.12)
                self.hit.clear()
            for enemy in world.enemies:
                if enemy.health > 0 and enemy.id not in self.hit and enemy.overlaps_circle(self.pos,self.radius):
                    self.hit.add(enemy.id)
                    world.hit_enemy(enemy,self.damage*(.65+self.heat*.35))
                    world.move_body(enemy,normalized(self.vel)*(16+self.heat*20),enemy.radius)
                    if self.heat < .28:
                        self.shatter(world)
                        return
                    self.heat -= .2
                    self.vel *= .88

    def shatter(self, world):
        if not self.alive:
            return
        self.alive = False
        world.burst(self.pos,(255,153,91) if self.heat>.15 else (171,219,219),10)
        for enemy in world.enemies:
            if enemy.health > 0 and enemy.pos.distance_to(self.pos)<enemy.radius+28:
                world.hit_enemy(enemy,self.damage*.35)

    def draw(self, graphics, surface, world):
        hot = (255,154+int(65*(1-self.heat)),94)
        cold = (135,206,215)
        color = hot if self.heat>.25 else cold
        pygame.draw.circle(surface,(88,49,37) if self.heat>.25 else (33,65,74),self.pos,int(self.radius+3))
        image = graphics.render_sprite(self.art.frame(int(self.age*12)%4,columns=4),int(self.radius*3),color)
        surface.blit(image,image.get_rect(center=self.pos))
        pygame.draw.circle(surface,color,self.pos,int(self.radius),2)
