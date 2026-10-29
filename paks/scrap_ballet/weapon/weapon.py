"""Collect physical drifting scrap before gathering and slinging it."""
import math
import random

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
        self.charge = self.cooldown = self.heat = 0.
        self.locked = False
        self.active = []
        self.seeded = False

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0)*10)%4, columns=4)

    def aim(self, world):
        intent = world.component('pilot').aim_direction(world)
        if intent is not None:
            return normalized(intent)
        targets = [e for e in world.enemies if e.health > 0]
        if world.prefs.aim_assist and targets:
            target = min(targets, key=lambda e: e.pos.distance_squared_to(world.player.pos))
            return normalized(target.pos-world.player.pos)
        return unit(world.player.angle)

    def capacity(self, world):
        return 3 + min(3, world.powerups_collected//2)

    def orbiters(self):
        return [s for s in self.active if s.alive and s.state == 'orbit']

    def seed_scrap(self, world):
        rng = random.Random(f'{world.seed}:salvage:{world.wave}')
        for index in range(16 + min(12, world.wave)):
            desired = (world.player.pos+unit(index*math.tau/6)*110 if index < 6 else
                       Vec(rng.uniform(35, WIDTH-35), rng.uniform(35, HEIGHT-35)))
            position = world.safe_position(desired, 9)
            self.add_scrap(world, position, unit(rng.random()*math.tau)*rng.uniform(18, 42))
        self.seeded = True

    def add_scrap(self, world, position, velocity):
        if len(self.active) >= 64:
            return
        piece = Salvage(self, position, velocity)
        self.active.append(piece)
        world.projectiles.append(piece)

    def on_enemy_destroyed(self, world, enemy):
        self.prune(world)
        for index in range(3):
            direction = unit(index*math.tau/3+enemy.id*.71)
            position = world.safe_position(enemy.pos+direction*12, 9)
            self.add_scrap(world, position, direction*38)

    def create_powerup(self, world, position):
        return Upgrade(position, self.art, world.pak('weapon').color, self.pickup_sound)

    def on_powerup(self, world, count):
        world.burst(world.player.pos, world.pak('weapon').color, 12)

    def on_level_start(self, world):
        self.active.clear()
        self.seeded = self.previous_fire = False
        self.charge = 0.
        self.seed_scrap(world)

    def on_shuffle(self, world, changed):
        self.active.clear()
        self.seeded = self.previous_fire = False
        self.charge = 0.
        self.seed_scrap(world)

    def deactivate(self, world):
        for piece in self.active:
            piece.alive = False
        self.active.clear()

    def prune(self, world):
        self.active = [s for s in self.active if s.alive and s in world.projectiles]

    def update(self, world, dt, control):
        lost = any(s.alive and s not in world.projectiles for s in self.active)
        self.prune(world)
        if not self.seeded or lost:
            self.seed_scrap(world)
        if not any(isinstance(s, Readout) and s.weapon is self for s in world.projectiles):
            world.projectiles.append(Readout(self))
        if control.fire:
            self.charge = min(1.2, self.charge+dt)
        elif self.previous_fire:
            gathered = self.orbiters()
            for index, piece in enumerate(gathered):
                piece.launch(world, self.aim(world).rotate((index-(len(gathered)-1)/2)*5))
            if gathered:
                self.sound.play(volume=.4)
            self.charge = 0.
        for piece in self.active:
            piece.attracted = (control.fire and piece.state == 'free' and
                               len(self.orbiters()) < self.capacity(world) and
                               piece.pos.distance_to(world.player.pos) < 145+min(40, world.powerups_collected*4))
        self.previous_fire = control.fire

    def demo_controls(self, world, controls):
        gathered = self.orbiters()
        loose = [s for s in self.active if s.state == 'free']
        if not gathered and loose:
            target = min(loose, key=lambda s: s.pos.distance_squared_to(world.player.pos))
            direction = target.pos-world.player.pos-world.player.vel*.3
            controls.x = float(direction.x > 12)-float(direction.x < -12)
            controls.y = float(direction.y > 12)-float(direction.y < -12)
            controls.fire = True
        else:
            controls.fire = world.time%1.6 < 1.15
        return controls


class Salvage(ProjectileBase):
    def __init__(self, weapon, position, velocity=None):
        super().__init__(position, velocity or Vec(), 8)
        self.weapon = weapon
        self.state = 'free'
        self.attracted = False
        self.age = self.pickup_delay = 0.
        self.slot = self.upgrades = 0
        self.damage = 0.
        self.bounces = 3

    @property
    def launched(self):
        return self.state == 'launched'

    def launch(self, world, direction):
        self.state, self.age = 'launched', 0.
        self.upgrades = world.powerups_collected
        self.damage = 34+10*self.weapon.charge+6*self.upgrades
        self.vel = direction*(420+self.weapon.charge*110)+world.player.vel*.35
        self.bounces = 3

    def settle(self):
        self.state, self.age, self.pickup_delay = 'free', 0., .4
        self.vel = normalized(self.vel)*45
        self.attracted = False

    def update(self, world, dt):
        self.age += dt
        self.pickup_delay = max(0., self.pickup_delay-dt)
        if self.state == 'orbit':
            old = self.pos.copy()
            angle = world.time*3.8+self.slot*math.tau/self.weapon.capacity(world)
            self.pos = world.player.pos+unit(angle)*(35+self.slot*4)
            self.vel = (self.pos-old)/dt if dt else Vec()
            return
        if self.state == 'free':
            if self.attracted and self.pickup_delay <= 0:
                self.vel += normalized(world.player.pos-self.pos)*650*dt
                self.vel *= math.exp(-2*dt)
                if self.vel.length() > 220:
                    self.vel.scale_to_length(220)
                if self.pos.distance_to(world.player.pos) < world.player.radius+self.radius+6:
                    occupied = {s.slot for s in self.weapon.orbiters()}
                    if len(occupied) < self.weapon.capacity(world):
                        self.slot = next(i for i in range(self.weapon.capacity(world)) if i not in occupied)
                        self.state = 'orbit'
                        self.weapon.sound.play(volume=.12)
                        return
            else:
                self.vel *= math.exp(-.07*dt)
        old = self.pos.copy()
        motion = world.move_body(self, self.vel*dt, self.radius)
        for normal in motion.normals:
            if self.vel.dot(normal) < 0:
                self.vel -= 2*normal*self.vel.dot(normal)
        if self.state != 'launched':
            return
        if motion.normals:
            self.bounces -= 1
            for wall in world.geometry:
                if wall.health > 0 and wall.overlaps_segment(old, self.pos+self.vel*.03):
                    world.hit_cover(wall, self.damage)
        for enemy in world.enemies:
            if enemy.health > 0 and enemy.pos.distance_to(self.pos) < enemy.radius+self.radius:
                world.hit_enemy(enemy, self.damage)
                world.move_body(enemy, normalized(enemy.pos-self.pos)*22, enemy.radius)
                self.vel *= -1
                self.settle()
                return
        if self.age > 2.4 or self.bounces < 0:
            self.settle()

    def draw(self, graphics, surface, world):
        if self.state == 'orbit':
            pygame.draw.line(surface, (70,120,150), world.player.pos, self.pos, 1)
        elif self.state == 'launched':
            pygame.draw.line(surface, (145,110,60), self.pos-self.vel*.04, self.pos, 3)
        size = 16 if self.state == 'free' else 25
        image = graphics.render_sprite(self.weapon.sprite(world), size, world.pak('weapon').color)
        surface.blit(image, image.get_rect(center=self.pos))
