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
        if self.locked and self.heat <= .12: self.locked = False
        firing = control.fire and not self.locked
        self.heat = max(0., min(1., self.heat + dt*(.32 if firing else -.47)))
        if self.heat >= 1: self.locked = True
        ray = next((s for s in self.active if isinstance(s, Ray)), None)
        if firing and ray is None:
            ray=Ray(self)
            self.active.append(ray)
            world.projectiles.append(ray)
            self.sound.play(volume=.18)
        if ray:
            ray.firing = firing
            if not firing: ray.alive=False
        self.previous_fire=control.fire


def distance_segment(point, start, end):
    delta=end-start
    t=max(0.,min(1.,(point-start).dot(delta)/max(.0001,delta.length_squared())))
    return point.distance_to(start+delta*t)


class Ray(ProjectileBase):
    def __init__(self, weapon):
        super().__init__(Vec(),Vec(),2)
        self.weapon, self.firing, self.segments=weapon, True, []

    def update(self, world, dt):
        if not self.firing:
            self.alive=False
            return
        start=world.player.pos.copy()
        direction=self.weapon.aim(world)
        self.segments=[]
        hit=set()
        for bounce in range(4+min(3,world.powerups_collected//2)):
            # Rectangles are broad phase only. March just the candidate shape's
            # clipped interval so custom rail/hole geometry remains respected.
            choices=[]
            for axis,limit in ((0,2 if direction.x<0 else WIDTH-2),(1,2 if direction.y<0 else HEIGHT-2)):
                if abs(direction[axis])>.00001:
                    distance=(limit-start[axis])/direction[axis]
                    if distance>0:choices.append((distance,axis))
            if not choices:break
            travel,axis=min(choices)
            end=start+direction*travel
            normal=Vec()
            normal[axis]=-1 if direction[axis]>0 else 1
            struck=None
            for wall in world.geometry:
                if wall.health<=0 or not wall.blocks_projectile(self):continue
                clip=wall.rect.inflate(4,4).clipline(start,end)
                if not clip:continue
                near=max(0.,(Vec(clip[0])-start).dot(direction)-3)
                far=min(travel,(Vec(clip[1])-start).dot(direction)+3)
                distance=near
                while distance<=far:
                    point=start+direction*distance
                    if wall.overlaps_circle(point,2):
                        travel=distance
                        end=point
                        distances=(abs(point.x-wall.rect.left),abs(point.x-wall.rect.right),abs(point.y-wall.rect.top),abs(point.y-wall.rect.bottom))
                        normal=(Vec(-1,0),Vec(1,0),Vec(0,-1),Vec(0,1))[distances.index(min(distances))]
                        struck=wall
                        break
                    distance+=2
            if struck is not None:world.hit_cover(struck,(13+world.powerups_collected*2)*dt)
            self.segments.append((start.copy(),end.copy()))
            for enemy in world.enemies:
                if enemy.id not in hit and distance_segment(enemy.pos,start,end)<enemy.radius+3:
                    world.hit_enemy(enemy,(37+world.powerups_collected*9)*(3**bounce)*dt)
                    hit.add(enemy.id)
            if normal is None: break
            direction -= 2*normal*direction.dot(normal)
            start=end+direction*5

    def draw(self, graphics, surface, world):
        for i,(start,end) in enumerate(self.segments):
            color=(255,178,211) if i else (130,245,238)
            pygame.draw.line(surface,tuple(int(c*.35) for c in color),start,end,7)
            pygame.draw.line(surface,color,start,end,2)
            pygame.draw.circle(surface,(240,250,255),end,4)
