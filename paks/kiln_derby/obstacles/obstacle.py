"""Furnaces eject hot rolling slag; shots turn it into real protective ceramic cover."""
import math
import random
import pygame
from system_panic.model import Cover, Vec, WIDTH, HEIGHT, unit, normalized
from system_panic.pak_api import ObstaclesBase


class Bellow(Cover):
    def __init__(self, center, heading, wait):
        super().__init__(pygame.Rect(center[0]-25, center[1]-22, 50, 44), 140, 140)
        self.heading = heading
        self.wait = wait
        self.burst_remaining = self.next_emit = self.flash = 0.
        self.turn_sign = 1
        self.turn_start = self.turn_target = heading
        self.turn_elapsed = self.turn_duration = 0.
        self.volleys = 0


class Slag(Cover):
    def __init__(self, position, velocity):
        super().__init__(pygame.Rect(0, 0, 34, 34), 64, 64)
        self.pos, self.vel = Vec(position), Vec(velocity)
        self.radius = 16.
        self.hot = True
        self.age = self.cold_age = 0.
        self.hits = set()
        self.sync_rect()

    def sync_rect(self):
        # Conservative metadata even between integer pixel centers.
        left, top = math.floor(self.pos.x-self.radius), math.floor(self.pos.y-self.radius)
        right, bottom = math.ceil(self.pos.x+self.radius), math.ceil(self.pos.y+self.radius)
        self.rect.update(left, top, right-left, bottom-top)

    def overlaps_circle(self, position, radius):
        return self.pos.distance_squared_to(position) < (self.radius+radius)**2

    def overlaps_segment(self, start, end):
        start, end = Vec(start), Vec(end)
        delta = end-start
        fraction = max(0., min(1., (self.pos-start).dot(delta)/max(.0001, delta.length_squared())))
        return self.pos.distance_squared_to(start+delta*fraction) < self.radius**2

    def navigation_key(self):
        return ('kiln-slag-circle', self.pos.x, self.pos.y, self.radius)

    def blocks_body(self, body):
        return not self.hot and body is not self

    def blocks_projectile(self, projectile):
        return projectile is not self


class Kilnworks(ObstaclesBase):
    MAX_SLAG = 8
    ROLL_SPEED = 300.
    HOT_SECONDS = 1.35
    COVER_SECONDS = 7.5

    def init(self):
        self.art = self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        frame = 0
        if world is not None and isinstance(entity, Bellow) and entity.flash > 0:
            frame = 2+int(world.time*14)%2
        return self.art.frame(frame, columns=4)

    def build(self, world):
        rng = random.Random(f'{world.seed}:kiln-slag-foundry:{world.wave}')
        centers = [(280+rng.randint(-35,35), 145+rng.randint(-25,25)),
                   (680+rng.randint(-35,35), 330+rng.randint(-25,25))]
        if world.wave >= 6:
            centers.append((480+rng.randint(-25,25), 240+rng.randint(-25,25)))
        mouths = [Bellow(center, rng.randrange(4)*math.pi/2, rng.uniform(.55, 1.6)) for center in centers]
        # Choose each servo's rotation once from the private layout RNG. Runtime
        # volley progression never consumes combat RNG or depends on draw calls.
        for mouth in mouths:
            mouth.turn_sign = rng.choice((-1, 1))
        return mouths

    def take_damage(self, world, obstacle, damage):
        if damage <= 0 or obstacle.health <= 0:
            return 0.
        if isinstance(obstacle, Slag) and obstacle.hot:
            # A timely shot changes a moving danger into an actual shield.
            self.cool(world, obstacle)
            return 0.
        applied = min(obstacle.health, damage)
        obstacle.health -= applied
        if obstacle.health <= 0:
            world.burst(Vec(obstacle.rect.center), (255, 184, 111), 12)
            world.events.append('impact')
        return applied

    def cool(self, world, slag):
        if not slag.hot or slag.health <= 0:
            return
        old_heading = normalized(slag.vel)
        slag.hot = False
        slag.vel = Vec()
        slag.cold_age = 0.
        # It becomes solid only at a geometrically safe position. Each body's
        # clearance is then resolved, so cooling never embeds an actor.
        slag.pos = world.safe_position(slag.pos, slag.radius+1, body=slag)
        slag.sync_rect()
        for body in (world.player, *world.enemies):
            if body.health > 0 and body.overlaps_circle(slag.pos, slag.radius+1):
                away = normalized(body.pos-slag.pos, -old_heading)
                for margin in (4, 20, 48, 96):
                    desired = slag.pos+away*(slag.radius+body.radius+margin)
                    body.pos = world.safe_position(desired, body.radius+2, body=body)
                    if not body.overlaps_circle(slag.pos, slag.radius+1):
                        break
        world.burst(slag.pos, (143, 218, 226), 8)

    def strike(self, world, slag, body):
        if body.health <= 0 or id(body) in slag.hits:
            return
        slag.hits.add(id(body))
        heading = normalized(slag.vel)
        if body is world.player:
            factor = {'relaxed': .8, 'standard': 1., 'intense': 1.25}.get(world.prefs.difficulty, 1.)
            world.hit_player((12+world.wave*.4)*factor)
        else:
            world.hit_enemy(body, 27+world.wave)
        world.move_body(body, heading*96, body.radius)
        body.vel += heading*260
        world.burst(body.pos, (255, 165, 91), 9)

    def emit(self, world, mouth):
        if sum(isinstance(wall, Slag) and wall.health > 0 for wall in world.cover) >= self.MAX_SLAG:
            return
        direction = unit(mouth.heading)
        position = Vec(mouth.rect.center)+direction*50
        slag = Slag(position, direction*self.ROLL_SPEED)
        if (not slag.radius+2 <= position.x <= WIDTH-slag.radius-2
                or not slag.radius+2 <= position.y <= HEIGHT-slag.radius-2):
            return
        if any(wall is not mouth and wall.health > 0 and wall.blocks_body(slag)
               and wall.overlaps_circle(position, slag.radius+2) for wall in world.geometry):
            return
        mouth.flash = .14
        # An actor trying to plug the muzzle is visibly blasted out first;
        # material is never silently spawned as solid cover inside that actor.
        for body in (world.player, *world.enemies):
            if body.overlaps_circle(position, slag.radius+3):
                self.strike(world, slag, body)
        world.cover.append(slag)

    def advance_slag(self, world, slag, dt):
        if not slag.hot:
            slag.cold_age += dt
            if slag.cold_age >= self.COVER_SECONDS:
                slag.health = 0
                world.burst(slag.pos, (104, 165, 176), 4)
            return
        slag.age += dt
        steps = max(1, math.ceil(slag.vel.length()*dt/4))
        for _ in range(steps):
            previous = slag.pos.copy()
            candidate = previous+slag.vel*(dt/steps)
            outside = not slag.radius <= candidate.x <= WIDTH-slag.radius or not slag.radius <= candidate.y <= HEIGHT-slag.radius
            wall = next((wall for wall in world.geometry if wall is not slag and wall.health > 0
                         and wall.blocks_body(slag) and wall.overlaps_circle(candidate, slag.radius)), None)
            if outside or wall is not None:
                self.cool(world, slag)
                return
            slag.pos = candidate
            slag.sync_rect()
            for body in (world.player, *world.enemies):
                if body.health > 0 and body.overlaps_circle(slag.pos, slag.radius):
                    self.strike(world, slag, body)
        if slag.age >= self.HOT_SECONDS:
            self.cool(world, slag)

    def update(self, world, dt):
        for mouth in tuple(world.cover):
            if not isinstance(mouth, Bellow) or mouth.health <= 0:
                continue
            mouth.flash = max(0., mouth.flash-dt)
            if mouth.burst_remaining <= 0:
                mouth.wait -= dt
                if mouth.turn_duration > 0:
                    mouth.turn_elapsed = min(mouth.turn_duration, mouth.turn_elapsed+dt)
                    fraction = mouth.turn_elapsed/mouth.turn_duration
                    eased = fraction*fraction*(3-2*fraction)
                    mouth.heading = mouth.turn_start+(mouth.turn_target-mouth.turn_start)*eased
                if mouth.wait <= 0:
                    if mouth.turn_duration > 0:
                        mouth.heading = mouth.turn_target
                        mouth.turn_duration = mouth.turn_elapsed = 0.
                    mouth.burst_remaining = 1.02
                    mouth.next_emit = 0.
                    mouth.volleys += 1
            if mouth.burst_remaining > 0:
                mouth.burst_remaining -= dt
                mouth.next_emit -= dt
                if mouth.next_emit <= 0:
                    self.emit(world, mouth)
                    mouth.next_emit += .36
                if mouth.burst_remaining <= 0:
                    mouth.wait = max(1.5, 2.7-world.wave*.018)
                    mouth.turn_start = mouth.heading
                    mouth.turn_target = mouth.heading+mouth.turn_sign*math.pi/2
                    mouth.turn_elapsed = 0.
                    mouth.turn_duration = mouth.wait
        for slag in tuple(world.cover):
            if isinstance(slag, Slag) and slag.health > 0:
                self.advance_slag(world, slag, dt)
        world.cover = [wall for wall in world.cover if wall.health > 0]

    def draw_floor(self, graphics, surface, world):
        for wall in world.cover:
            if isinstance(wall, Slag):
                pygame.draw.ellipse(surface, (16, 20, 26), (wall.pos.x-19, wall.pos.y+9, 38, 13))
            elif isinstance(wall, Bellow) and wall.flash > 0:
                position = Vec(wall.rect.center)+unit(wall.heading)*50
                pygame.draw.circle(surface, (107, 43, 26), position, 20)
                pygame.draw.circle(surface, (255, 161, 78), position, 19, 2)

    def draw(self, graphics, surface, world, obstacle):
        if isinstance(obstacle, Slag):
            color = (255, 138, 65) if obstacle.hot else (129, 191, 198)
            fill = (161, 67, 36) if obstacle.hot else (51, 83, 99)
            pygame.draw.circle(surface, fill, obstacle.pos, int(obstacle.radius))
            pygame.draw.circle(surface, color, obstacle.pos, int(obstacle.radius), 2)
            phase = obstacle.age*220 if obstacle.hot else 0.
            for angle in (phase, phase+120, phase+240):
                direction = unit(math.radians(angle))
                a, b = obstacle.pos+direction*12, obstacle.pos+direction.rotate(45)*5
                pygame.draw.line(surface, color, a, b, 2)
            if obstacle.hot:
                pygame.draw.circle(surface, (255, 225, 151), obstacle.pos, 5)
            else:
                pygame.draw.circle(surface, (185, 223, 224), obstacle.pos+Vec(-4,-4), 4, 1)
            return
        center = Vec(obstacle.rect.center)
        pygame.draw.rect(surface, (63, 40, 35), obstacle.rect, border_radius=10)
        image = graphics.render_sprite(self.sprite(world, obstacle), 58, (255, 175, 105))
        image = pygame.transform.rotate(image, -math.degrees(obstacle.heading))
        surface.blit(image, image.get_rect(center=center))
        direction = unit(obstacle.heading)
        pygame.draw.circle(surface, (246, 139, 80), center+direction*18, 6, 2)
        if obstacle.health < obstacle.max_health*.55:
            pygame.draw.line(surface, (28,25,27), center-Vec(10,12), center+Vec(5,4), 2)
            pygame.draw.line(surface, (28,25,27), center+Vec(5,4), center+Vec(13,16), 2)
