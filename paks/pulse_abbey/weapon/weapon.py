"""Component-local weapon state; no host behavior registry or sibling imports."""
import math
import pygame
from system_panic.model import Vec, WIDTH, HEIGHT, normalized, unit
from system_panic.pak_api import WeaponBase, ProjectileBase
from .powerup import Upgrade
from .readout import Readout


class Weapon(WeaponBase):
    MIN_CHARGE = .45
    MAX_CHARGE = 1.2

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
        self.fizzle = 0.

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
        self.cooldown = max(0., self.cooldown - dt)
        self.fizzle = max(0., self.fizzle - dt)
        if control.fire and self.cooldown <= 0:
            self.charge = min(self.MAX_CHARGE, self.charge + dt)
        if self.previous_fire and not control.fire:
            if self.charge + 1e-8 >= self.MIN_CHARGE and self.cooldown <= 0:
                phase = (world.time % .6) / .6
                perfect = min(phase, 1-phase) < .17
                world.projectiles.append(Resonance(world.player.pos, self.charge, perfect, world.powerups_collected))
                self.sound.play(volume=.45 if perfect else .27)
                self.cooldown = .3
            else:
                self.fizzle = .25
            self.charge = 0.
        self.previous_fire = control.fire

    def demo_controls(self, world, controls):
        controls.fire = world.time % 1.8 < 1.14
        targets=[e for e in world.enemies if e.health>0]
        if targets:
            delta=min(targets,key=lambda e:e.pos.distance_squared_to(world.player.pos)).pos-world.player.pos
            toward=normalized(delta)
            distance=delta.length()
            direction=toward if distance>125 else -toward if distance<80 else Vec(-toward.y,toward.x)
            controls.x=float(direction.x>.2)-float(direction.x<-.2)
            controls.y=float(direction.y>.2)-float(direction.y<-.2)
        return controls


class Resonance(ProjectileBase):
    def __init__(self, position, charge, perfect, upgrades):
        super().__init__(position, Vec(), 1)
        strength=max(0.,min(1.,(charge-Weapon.MIN_CHARGE)/(Weapon.MAX_CHARGE-Weapon.MIN_CHARGE)))
        self.reach = 70 + 110 * strength + min(240, upgrades * 20)
        self.damage = (18 + 50 * strength + upgrades * 5) * (1.6 if perfect else .2)
        self.perfect, self.hit = perfect, set()

    def update(self, world, dt):
        before = self.radius
        self.radius = min(self.reach,self.radius+510*dt)
        if self.perfect:
            for shot in tuple(world.projectiles):
                if shot is self or not shot.alive or not shot.is_threat_to(world,world.player):continue
                distance=shot.pos.distance_to(self.pos)
                if before-shot.radius<=distance<=self.radius+shot.radius:
                    shot.alive=False
                    world.score+=10
                    world.burst(shot.pos,(255,228,150),4)
        for enemy in world.enemies:
            distance = enemy.pos.distance_to(self.pos)
            if enemy.id not in self.hit and before - enemy.radius <= distance <= self.radius + enemy.radius:
                world.hit_enemy(enemy, self.damage)
                self.hit.add(enemy.id)
                world.move_body(enemy, normalized(enemy.pos-self.pos)*18, enemy.radius)
        if self.radius >= self.reach: self.alive = False

    def draw(self, graphics, surface, world):
        color = (255, 228, 150) if self.perfect else world.pak('weapon').color
        pygame.draw.circle(surface, color, self.pos, int(self.radius), 4 if self.perfect else 2)
        pygame.draw.circle(surface, tuple(int(c*.35) for c in color), self.pos, max(1,int(self.radius-9)), 1)
