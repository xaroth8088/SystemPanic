"""Paired fold doors carry every actor; shots briefly open moving paper shutters."""
import math
import random
import pygame
from system_panic.model import Cover, Vec
from system_panic.pak_api import ObstaclesBase


class FoldGate(Cover):
    def __init__(self, center, pair, bearing):
        super().__init__(pygame.Rect(center[0]-27, center[1]-27, 54, 54), 100, 100)
        self.pair, self.bearing = pair, bearing
    def blocks_body(self, body): return False
    def blocks_projectile(self, projectile): return False


class Shutter(Cover):
    def __init__(self, rect, phase):
        super().__init__(pygame.Rect(rect), 100, 100)
        self.home = Vec(self.rect.center)
        self.phase, self.opened = phase, 0.
    def blocks_body(self, body): return self.opened <= 0
    def blocks_projectile(self, projectile): return self.opened <= 0


class PaperObstacles(ObstaclesBase):
    def init(self):
        self.art = self.load_asset('obstacles_sheet.png')
        self.age = 0.
        self.cooldowns = {}

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0)*5)%4, columns=4)

    def build(self, world):
        rng = random.Random(f'{world.seed}:paper_pilgrimage:{world.wave}')
        self.age = 0.
        self.cooldowns.clear()
        y = rng.randrange(105, 170)
        gates = [FoldGate((145, y), 1, 0), FoldGate((815, 480-y), 0, math.pi),
                 FoldGate((350, 390), 3, -math.pi/2), FoldGate((610, 90), 2, math.pi/2)]
        shutters = [Shutter((290+rng.randrange(-20, 21), 155, 16, 100), rng.random()*math.tau),
                    Shutter((650+rng.randrange(-20, 21), 230, 16, 100), rng.random()*math.tau)]
        return gates+shutters

    def take_damage(self, world, obstacle, damage):
        if isinstance(obstacle, Shutter) and damage > 0:
            obstacle.opened = max(obstacle.opened, 1.25)
            world.burst(Vec(obstacle.rect.center), world.pak('obstacles').color, 4)
        return 0.

    def update(self, world, dt):
        self.age += dt
        bodies = (world.player, *world.enemies)
        present = {id(body) for body in bodies}
        self.cooldowns = {key:remaining-dt for key, remaining in self.cooldowns.items()
                          if key in present and remaining > dt}
        gates = [wall for wall in world.cover if isinstance(wall, FoldGate)]
        for wall in world.cover:
            if isinstance(wall, Shutter):
                wall.opened = max(0., wall.opened-dt)
                wall.rect.centery = round(wall.home.y+40*math.sin(self.age*.5+wall.phase))
        # Resolve a moving/closing shutter before considering gate arrivals.
        for body in bodies:
            if any(w.health > 0 and w.blocks_body(body) and w.overlaps_circle(body.pos, body.radius+1) for w in world.cover):
                body.pos = world.safe_position(body.pos, body.radius+2, body=body)
            if id(body) in self.cooldowns or body.health <= 0: continue
            for gate in gates:
                center = Vec(gate.rect.center)
                if body.pos.distance_squared_to(center) < (21+body.radius*.35)**2 and gate.pair < len(gates):
                    destination = gates[gate.pair]
                    direction = Vec(math.cos(destination.bearing), math.sin(destination.bearing))
                    desired = Vec(destination.rect.center)+direction*(37+body.radius)
                    body.pos = world.safe_position(desired, body.radius+2, body=body)
                    body.vel = body.vel.rotate_rad(destination.bearing-gate.bearing+math.pi)
                    self.cooldowns[id(body)] = .85
                    world.burst(center, world.pak('obstacles').color, 6)
                    world.burst(body.pos, world.pak('obstacles').color, 6)
                    break

    def draw_floor(self, graphics, surface, world):
        gates = [wall for wall in world.cover if isinstance(wall, FoldGate)]
        for index, gate in enumerate(gates):
            if index < gate.pair < len(gates):
                a, b = Vec(gate.rect.center), Vec(gates[gate.pair].rect.center)
                for segment in range(0, 20, 2):
                    pygame.draw.line(surface, (38, 48, 65), a.lerp(b, segment/20), a.lerp(b, (segment+1)/20), 1)

    def draw(self, graphics, surface, world, wall):
        color = world.pak('obstacles').color
        if isinstance(wall, FoldGate):
            center = Vec(wall.rect.center)
            rotation = wall.bearing*180/math.pi
            points = [center+Vec(31, 0).rotate(rotation+turn*90) for turn in range(4)]
            pygame.draw.polygon(surface, (26, 34, 49), points)
            pygame.draw.polygon(surface, color if wall.pair < 2 else (250, 192, 130), points, 3)
            art = self.art.frame(1+int(world.time*4)%3, columns=4)
            image = graphics.render_sprite(art, 54, color)
            surface.blit(image, image.get_rect(center=center))
        else:
            color = tuple(int(c*(.25 if wall.opened > 0 else .8)) for c in color)
            pygame.draw.rect(surface, (27, 34, 48), wall.rect, border_radius=3)
            pygame.draw.rect(surface, color, wall.rect, 2, border_radius=3)
            for y in range(wall.rect.top+8, wall.rect.bottom-2, 12):
                pygame.draw.line(surface, color, (wall.rect.left+3, y), (wall.rect.right-3, y+6), 1)
