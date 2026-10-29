"""Shot-turned wind gates change real lanes and launch actors along jet corridors."""
import math
import random
import pygame
from system_panic.model import Cover, Vec, WIDTH, HEIGHT, circle_rect
from system_panic.pak_api import ObstaclesBase


class Vane(Cover):
    """The broad rect contains a hub and two exact, shot-rotated solid wings."""
    def __init__(self, center, heading, phase=0.):
        super().__init__(pygame.Rect(center[0]-104, center[1]-104, 208, 208), 1000, 1000)
        self.heading = heading
        self.turn_cooldown = 0.

    @property
    def direction(self):
        quarter = round(self.heading / (math.pi / 2)) % 4
        return (Vec(1, 0), Vec(0, 1), Vec(-1, 0), Vec(0, -1))[quarter]

    def pieces(self):
        x, y = self.rect.center
        hub = pygame.Rect(x-18, y-18, 36, 36)
        if self.direction.x:
            return (hub, pygame.Rect(x-7, y-104, 14, 74), pygame.Rect(x-7, y+30, 14, 74))
        return (hub, pygame.Rect(x-104, y-7, 74, 14), pygame.Rect(x+30, y-7, 74, 14))

    def overlaps_circle(self, position, radius):
        return any(circle_rect(position, radius, piece) for piece in self.pieces())

    def overlaps_segment(self, start, end):
        return any(piece.clipline(start, end) for piece in self.pieces())

    def navigation_key(self):
        return ('storm-solid-wind-gate', self.rect.center, round(self.heading/(math.pi/2))%4)

    def damage(self, world, amount):
        if amount > 0 and self.turn_cooldown <= 0:
            self.heading += math.pi / 2
            self.turn_cooldown = .4
            # New physical wings may occupy an actor's old lane. Resolve that
            # geometry immediately instead of embedding a body.
            for body in (world.player, *world.enemies):
                if body.health > 0 and self.overlaps_circle(body.pos, body.radius+1):
                    body.pos = world.safe_position(body.pos, body.radius+2, body=body)
            world.burst(Vec(self.rect.center), (150, 233, 255), 10)
        return 0.


class Windworks(ObstaclesBase):
    JET_SPEED = 560.
    JET_HALF_WIDTH = 34.

    def init(self):
        self.art = self.load_asset('obstacles_sheet.png')
        self.impacts = {}

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0) * 8) % 4, columns=4)

    def build(self, world):
        self.impacts.clear()
        rng = random.Random(f'{world.seed}:storm-loom-gates:{world.wave}')
        centers = [(250+rng.randint(-30,30), 145+rng.randint(-20,20)),
                   (710+rng.randint(-30,30), 330+rng.randint(-20,20))]
        if world.wave >= 5:
            centers.append((480+rng.randint(-25,25), 240+rng.randint(-20,20)))
        return [Vane(center, rng.randrange(4)*math.pi/2) for center in centers]

    def deactivate(self, world):
        self.impacts.clear()

    @staticmethod
    def jet_length(vane):
        center, direction = Vec(vane.rect.center), vane.direction
        if direction.x:
            return WIDTH-center.x if direction.x > 0 else center.x
        return HEIGHT-center.y if direction.y > 0 else center.y

    def update(self, world, dt):
        bodies = (world.player, *world.enemies)
        present = {id(body) for body in bodies}
        self.impacts = {key: remaining-dt for key,remaining in self.impacts.items()
                        if key in present and remaining > dt}
        for vane in world.cover:
            if not isinstance(vane, Vane) or vane.health <= 0:
                continue
            vane.turn_cooldown = max(0., vane.turn_cooldown-dt)
            center, direction = Vec(vane.rect.center), vane.direction
            side = Vec(-direction.y, direction.x)
            length = self.jet_length(vane)
            for body in bodies:
                if body.health <= 0:
                    continue
                delta = body.pos-center
                along, across = delta.dot(direction), delta.dot(side)
                closest = center+direction*along
                if not 26 < along < length or not body.overlaps_circle(closest, self.JET_HALF_WIDTH):
                    continue
                # Crosswise steering can escape a concentrated stream;
                # following its axis commits to a fast traversal ride.
                centering = max(-80., min(80., across*3))
                motion = world.move_body(body, (direction*self.JET_SPEED-side*centering)*dt, body.radius)
                projected = body.vel.dot(direction)
                body.vel += direction*max(0., self.JET_SPEED-projected)*min(1., 6*dt)
                if motion.normals and id(body) not in self.impacts:
                    self.impacts[id(body)] = .9
                    if body is world.player:
                        factor = {'relaxed': .8, 'standard': 1., 'intense': 1.25}.get(world.prefs.difficulty, 1.)
                        world.hit_player((10+world.wave*.3)*factor)
                    else:
                        world.hit_enemy(body, 25+world.wave)
                    world.burst(body.pos, (215, 247, 255), 9)

    def take_damage(self, world, obstacle, damage):
        return 0.

    def draw_floor(self, graphics, surface, world):
        for vane in world.cover:
            if not isinstance(vane, Vane) or vane.health <= 0:
                continue
            center, direction = Vec(vane.rect.center), vane.direction
            side = Vec(-direction.y, direction.x)
            length = self.jet_length(vane)
            start, end = center+direction*26, center+direction*length
            points = [start-side*self.JET_HALF_WIDTH, end-side*self.JET_HALF_WIDTH,
                      end+side*self.JET_HALF_WIDTH, start+side*self.JET_HALF_WIDTH]
            pygame.draw.polygon(surface, (17, 53, 72), points)
            pygame.draw.line(surface, (47, 121, 147), points[0], points[1], 1)
            pygame.draw.line(surface, (47, 121, 147), points[3], points[2], 1)
            for lane in (-22, 0, 22):
                for index in range(max(1, int(length/65))):
                    travel = (index*65+world.time*self.JET_SPEED) % max(1., length-26)+26
                    a = center+direction*travel+side*lane
                    b = a+direction*min(25, max(0., length-travel))
                    pygame.draw.line(surface, (104, 197, 215), a, b, 2)

    def draw(self, graphics, surface, world, obstacle):
        center = Vec(obstacle.rect.center)
        for panel in obstacle.pieces()[1:]:
            pygame.draw.rect(surface, (27, 67, 77), panel, border_radius=3)
            pygame.draw.rect(surface, (118, 192, 196), panel, 2, border_radius=3)
            if panel.height > panel.width:
                for y in range(panel.top+6, panel.bottom-2, 10):
                    pygame.draw.line(surface, (65, 123, 137), (panel.left+3,y), (panel.right-3,y+4), 2)
            else:
                for x in range(panel.left+6, panel.right-2, 10):
                    pygame.draw.line(surface, (65, 123, 137), (x,panel.top+3), (x+4,panel.bottom-3), 2)
        pygame.draw.rect(surface, (24, 59, 77), obstacle.pieces()[0], border_radius=5)
        image = graphics.render_sprite(self.sprite(world), 45, (142, 225, 251))
        surface.blit(image, image.get_rect(center=center))
        direction = obstacle.direction
        side = Vec(-direction.y, direction.x)
        tip = center+direction*25
        pygame.draw.polygon(surface, (215, 249, 255), [tip, tip-direction*8+side*5, tip-direction*8-side*5])
