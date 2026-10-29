"""A magnetic tug carries momentum, then reverses its field in a sling pulse."""
import math
from system_panic.model import Pilot, Vec, Controls, normalized, WIDTH, HEIGHT
from system_panic.pak_api import PilotBase, EffectBase
import pygame


class FieldPulse(EffectBase):
    def __init__(self, position, color):
        self.pos, self.color, self.age, self.alive = Vec(position), color, 0., True
    def update(self, dt):
        self.age += dt
        self.alive = self.age < .28
    def draw(self, graphics, surface, world):
        pygame.draw.circle(surface, self.color, self.pos, max(1, int(95*self.age/.28)), 2)


class FerricPilot(PilotBase):
    controls = 'Arrows / WASD: thrust the magnetic tug'
    special = 'X: reverse momentum and repel nearby enemies'

    def init(self):
        self.art = self.load_asset('pilot_sheet.png')
        self.sound = self.load_asset('special.ogg')
        self.cooldown = 0.
        self.previous_special = False
        self.polarity = 1

    def create(self, world, position):
        return Pilot(pos=Vec(position), health=110, max_health=110, radius=12)

    def sprite(self, world, entity=None):
        actor=entity if entity is not None else (world.player if world is not None else None)
        angle=actor.angle if actor is not None else 0.
        facing=int((angle+math.tau/16)%math.tau/(math.tau/8))
        phase=int((world.time if world is not None else 0)*8)%4
        return self.art.frame(phase*8+facing, columns=8, rows=4)

    def sprite_angle(self,world,entity):return 0.

    def sprite_flip_x(self,world,entity):return False


    def on_level_start(self, world):
        if world.wave > 1:
            world.player.health = min(world.player.max_health, world.player.health+11)
        world.player.invulnerable = max(world.player.invulnerable, 1.4)

    def on_shuffle(self, world, changed):
        world.player.invulnerable = max(world.player.invulnerable, 1.1)

    def update(self, world, dt, control):
        p = world.player
        self.cooldown = max(0., self.cooldown-dt)
        direction = Vec(control.x, control.y)
        if direction.length_squared() > 1: direction.normalize_ip()
        if control.special and not self.previous_special and self.cooldown <= 0:
            self.polarity *= -1
            self.cooldown = 2.8
            p.vel *= -.65
            p.invulnerable = max(p.invulnerable, .25)
            for enemy in world.enemies:
                delta = enemy.pos-p.pos
                if enemy.health > 0 and delta.length_squared() < 110**2:
                    world.move_body(enemy, normalized(delta)*(110-delta.length())*.7, enemy.radius)
                    enemy.vel += normalized(delta)*90
            world.effects.append(FieldPulse(p.pos, world.pak('pilot').color))
            self.sound.play(volume=.5)
        self.previous_special = control.special
        p.vel = p.vel*math.exp(-3.6*dt)+direction*(900*dt)
        if p.vel.length_squared() > 255**2: p.vel.scale_to_length(255)
        motion = world.move_body(p, p.vel*dt, p.radius)
        for normal in motion.normals:
            if p.vel.dot(normal) < 0: p.vel -= normal*p.vel.dot(normal)*1.3
        if direction.length_squared(): p.angle = math.atan2(direction.y, direction.x)

    def take_damage(self, world, damage):
        applied = world.apply_damage(world.player, damage)
        if applied:
            world.player.invulnerable = .9
            world.shake = 5
            world.events.append('hurt')
            world.burst(world.player.pos, (255, 130, 125), 11)
        return applied

    def on_death(self, world):
        world.burst(world.player.pos, world.pak('pilot').color, 38)

    def status(self, world):
        return f'FIELD {"+" if self.polarity > 0 else "−"}  |  REVERSE {self.cooldown:.1f}s'

    def demo_controls(self, world):
        if not world.enemies: return Controls()
        p = world.player
        enemy = min(world.enemies, key=lambda e:e.pos.distance_squared_to(p.pos))
        delta = enemy.pos-p.pos
        toward = normalized(delta)
        direction = toward if delta.length() > 185 else Vec(-toward.y, toward.x)-toward*.25
        blockers = [wall for wall in world.geometry if wall.health > 0 and wall.blocks_body(p)
                    and wall.overlaps_segment(p.pos, enemy.pos)]
        if blockers and delta.length() > 140:
            wall = min(blockers, key=lambda w:Vec(w.rect.center).distance_squared_to(p.pos))
            points = [Vec(wall.rect.left-35, wall.rect.centery), Vec(wall.rect.right+35, wall.rect.centery),
                      Vec(wall.rect.centerx, wall.rect.top-35), Vec(wall.rect.centerx, wall.rect.bottom+35)]
            points = [point for point in points if 30 < point.x < WIDTH-30 and 30 < point.y < HEIGHT-30
                      and not any(w.health > 0 and w.blocks_body(p) and w.overlaps_segment(p.pos, point) for w in world.geometry)]
            if points:
                point = min(points, key=lambda v:v.distance_to(p.pos)+v.distance_to(enemy.pos))
                direction = normalized(point-p.pos)
        if p.pos.x < 45: direction.x = 1
        if p.pos.x > WIDTH-45: direction.x = -1
        if p.pos.y < 45: direction.y = 1
        if p.pos.y > HEIGHT-45: direction.y = -1
        return Controls(int(direction.x>.2)-int(direction.x<-.2), int(direction.y>.2)-int(direction.y<-.2), True,
                        delta.length() < 80 and self.cooldown <= 0)
