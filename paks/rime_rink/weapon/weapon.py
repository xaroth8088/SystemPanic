"""A finite set of physical curling stones: throw, stop, skate over, reuse."""
import math
import pygame
from system_panic.model import Body, Vec, normalized, unit, WIDTH, HEIGHT
from system_panic.pak_api import WeaponBase, ProjectileBase
from .powerup import Upgrade


def path_contact(body, start, end, radius):
    """Use real actor footprints along an actual motion segment."""
    query = body.overlaps_circle
    delta = end-start
    if getattr(query, "__func__", None) is Body.overlaps_circle:
        t = max(0., min(1., (body.pos-start).dot(delta)/max(.0001, delta.length_squared())))
        return query(start+delta*t, radius)
    steps = max(1, math.ceil(delta.length()/max(1., min(3., radius*.5))))
    return any(query(start.lerp(end, index/steps), radius) for index in range(steps+1))


class Weapon(WeaponBase):
    def init(self):
        self.art = self.load_asset("weapon_sheet.png")
        self.sound = self.load_asset("shot.ogg")
        self.chime = self.load_asset("pickup.ogg")
        self.cooldown = 0.
        self.stones = []
        self.capacity = self.stock = 4
        self.recovered = 0
        self.demo_retrieving = False

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0)*8)%4, columns=4)

    def sync_capacity(self, world):
        capacity = 4+min(2, world.powerups_collected)
        if capacity > self.capacity:
            # A collected upgrade may add a new physical stone. Elapsed time,
            # slowing down and projectile removal never return a spent stone.
            self.stock += capacity-self.capacity
        self.capacity = capacity

    def activate(self, world):
        self.sync_capacity(world)

    def create_powerup(self, world, position):
        return Upgrade(position, self.art, world.pak("weapon").color, self.chime)

    def on_powerup(self, world, count):
        self.sync_capacity(world)
        world.burst(world.player.pos, world.pak("weapon").color, 12)

    def reset(self, world):
        for stone in self.stones:
            stone.alive = False
        self.stones.clear()
        self.capacity = 4+min(2, world.powerups_collected)
        self.stock = self.capacity
        self.cooldown = 0.
        self.demo_retrieving = False

    def deactivate(self, world):
        for stone in self.stones:
            stone.alive = False
        self.stones.clear()
        self.stock = 0

    def on_level_start(self, world):
        self.reset(world)

    def on_shuffle(self, world, changed):
        if changed & {"pilot", "enemy", "weapon", "obstacles"}:
            # Gameplay replacement clears scheduled objects in the host. Treat
            # that explicit boundary like a fresh rack, with no orphaned loans.
            self.reset(world)
            return
        # A presentation-only shuffle also clears scheduled objects, but cannot
        # replenish this weapon. Restore these same physical stones and stock.
        for stone in self.stones:
            if stone.alive and stone not in world.projectiles:
                world.projectiles.append(stone)

    def recover(self, world, stone):
        if not stone.alive or not any(item is stone for item in self.stones):
            return False
        self.stones.remove(stone)
        stone.alive = False
        self.stock = min(self.capacity, self.stock+1)
        self.recovered += 1
        self.chime.play(volume=.24)
        world.burst(stone.pos, (181, 235, 255), 7)
        return True

    def update(self, world, dt, control):
        self.sync_capacity(world)
        self.cooldown = max(0., self.cooldown-dt)
        if not control.fire or self.cooldown > 0 or self.stock <= 0:
            return
        intent = world.component("pilot").aim_direction(world)
        if intent is not None:
            direction = normalized(intent)
        elif world.prefs.aim_assist and world.enemies:
            target = min(world.enemies, key=lambda e: e.pos.distance_squared_to(world.player.pos))
            direction = normalized(target.pos+target.vel*.16-world.player.pos)
        else:
            direction = unit(world.player.angle)
        stone = Stone(world.player.pos, direction*440+world.player.vel*.3,
                      29+6*world.powerups_collected, self.art, world.pak("weapon").color, owner=self)
        # Launch from the last genuinely clear point, including custom covers;
        # never create a stone inside a wall because the muzzle extends into it.
        desired = world.player.pos+direction*(world.player.radius+stone.radius+4)
        distance = desired.distance_to(stone.pos)
        steps = max(1, math.ceil(distance/2))
        start = stone.pos.copy()
        for index in range(steps+1):
            point = start.lerp(desired, index/steps)
            if not stone.clear(world, point):
                break
            stone.pos = point
        stone.left_thrower = not world.player.overlaps_circle(stone.pos, stone.radius+2)
        self.stock -= 1
        self.stones.append(stone)
        world.projectiles.append(stone)
        self.cooldown = max(.3, .65-world.powerups_collected*.035)
        self.sound.play(volume=.4)

    def demo_controls(self, world, controls):
        available = [stone for stone in self.stones if stone.alive and stone in world.projectiles]
        resting = [stone for stone in available if stone.resting]
        if self.stock == 0 or self.demo_retrieving and self.stock < min(2, self.capacity):
            self.demo_retrieving = True
        elif self.stock <= 1 and resting:
            self.demo_retrieving = True
        else:
            self.demo_retrieving = False
        if not self.demo_retrieving or not available:
            controls.fire = self.stock > 0
            return controls
        p = world.player
        target = min(resting or available, key=lambda stone: stone.pos.distance_squared_to(p.pos))
        delta = target.pos-p.pos
        distance = delta.length()
        heading = normalized(delta)
        speed = min(200., distance*3)
        desired = heading*speed-p.vel*.85
        # Probe around actual body geometry while pursuing a real rock. This
        # only emits ordinary digital input through the selected pilot.
        for angle in (0, 35, -35, 70, -70, 110, -110, 160):
            trial = normalized(desired).rotate(angle)
            probe = p.pos+trial*max(28, min(60, distance))
            if not any(wall.health > 0 and wall.blocks_body(p) and wall.overlaps_circle(probe, p.radius+3)
                       for wall in world.geometry):
                desired = trial*max(30., desired.length())
                break
        controls.x = (desired.x > 12)-(desired.x < -12)
        controls.y = (desired.y > 12)-(desired.y < -12)
        controls.special = distance < 90
        controls.fire = False
        return controls


class Stone(ProjectileBase):
    STOP_SPEED = 60.
    ARENA_MARGIN = 22.  # Keeps the entire rotating 30px stone visible at a bank.

    def __init__(self, position, velocity, damage, art, color, owner=None):
        super().__init__(position, velocity, 11)
        self.damage, self.art, self.color, self.owner = damage, art, color, owner
        self.age = 0.
        self.contacts = {}
        self.banks = 0
        self.resting = self.vel.length_squared() < self.STOP_SPEED**2
        self.left_thrower = False
        if self.resting:
            self.vel = Vec()

    def clear(self, world, point):
        return (self.ARENA_MARGIN <= point.x <= WIDTH-self.ARENA_MARGIN
                and self.ARENA_MARGIN <= point.y <= HEIGHT-self.ARENA_MARGIN
                and not any(wall.health > 0 and wall.blocks_projectile(self)
                            and wall.overlaps_circle(point, self.radius) for wall in world.geometry))

    def separate(self, world):
        """Local physical separation if moving/closing geometry enters a rock.

        This does not award ammo, chase a pilot or rescue an unreachable mix.
        Exact shape queries determine clearance; custom rects are only metadata.
        """
        self.pos.x = max(self.ARENA_MARGIN, min(WIDTH-self.ARENA_MARGIN, self.pos.x))
        self.pos.y = max(self.ARENA_MARGIN, min(HEIGHT-self.ARENA_MARGIN, self.pos.y))
        if self.clear(world, self.pos):
            return
        before = self.pos.copy()
        for distance in (1, 2, 4, 8, 16, 24, 40, 64, 96):
            for index in range(16):
                candidate = before+unit(index*math.tau/16)*distance
                if self.clear(world, candidate):
                    self.pos, self.vel, self.resting = candidate, Vec(), True
                    return
        self.vel, self.resting = Vec(), True

    def pickup(self, world, start, end):
        if self.owner is None:
            return False
        if not world.player.overlaps_circle(end, self.radius+2):
            self.left_thrower = True
        if not (self.left_thrower or self.banks or self.resting):
            return False
        if path_contact(world.player, start, end, self.radius):
            return self.owner.recover(world, self)
        return False

    def strike(self, world, start, end):
        speed = self.vel.length()
        if speed < self.STOP_SPEED:
            return
        direction = normalized(self.vel)
        for enemy in world.enemies:
            if enemy.health <= 0 or self.contacts.get(enemy.id, -10) > self.age-.4:
                continue
            if not path_contact(enemy, start, end, self.radius):
                continue
            self.contacts[enemy.id] = self.age
            world.hit_enemy(enemy, self.damage*min(1.35, .7+speed/700)*(1+self.banks*.12))
            world.move_body(enemy, direction*(28+self.banks*5), enemy.radius)
            enemy.vel += direction*min(180, speed*.45)
            self.vel *= .78
            world.burst(enemy.pos, self.color, 5)

    def update(self, world, dt):
        if not self.alive:
            return
        self.age += dt
        self.separate(world)
        if self.resting:
            self.vel = Vec()
            self.pickup(world, self.pos, self.pos)
            return
        # Every axis segment is real travel, including after a ricochet; never
        # test a straight chord through a wall between pre/post-bounce positions.
        subdivisions = max(1, math.ceil(self.vel.length()*dt/4))
        for _ in range(subdivisions):
            for axis, limit in ((0, WIDTH), (1, HEIGHT)):
                previous = self.pos.copy()
                proposed = previous.copy()
                proposed[axis] += self.vel[axis]*dt/subdivisions
                hit = next((wall for wall in world.geometry if wall.health > 0 and wall.blocks_projectile(self)
                            and wall.overlaps_circle(proposed, self.radius)), None)
                if hit is not None:
                    low, high = 0., 1.
                    for _ in range(12):
                        middle = (low+high)/2
                        if hit.overlaps_circle(previous.lerp(proposed, middle), self.radius):
                            high = middle
                        else:
                            low = middle
                    self.pos = previous.lerp(proposed, low)
                else:
                    self.pos = proposed
                    self.pos[axis] = max(self.ARENA_MARGIN, min(limit-self.ARENA_MARGIN, self.pos[axis]))
                if hit is not None or proposed[axis] < self.ARENA_MARGIN or proposed[axis] > limit-self.ARENA_MARGIN:
                    self.vel[axis] *= -.86
                    self.banks = min(4, self.banks+1)
                    if hit is not None:
                        world.hit_cover(hit, self.damage*.5)
                if self.pickup(world, previous, self.pos):
                    return
                self.strike(world, previous, self.pos)
        self.vel *= math.exp(-.22*dt)
        if self.vel.length_squared() < self.STOP_SPEED**2:
            self.resting, self.vel = True, Vec()
        present = {enemy.id for enemy in world.enemies}
        self.contacts = {identity: age for identity, age in self.contacts.items() if identity in present and age > self.age-.4}

    def draw(self, graphics, surface, world):
        if self.resting:
            pygame.draw.ellipse(surface, (16, 36, 49), (self.pos.x-15, self.pos.y+7, 30, 9))
            pygame.draw.circle(surface, (124, 202, 224), self.pos, 12, 1)
            frame = self.art.frame(0, columns=4)
        else:
            pygame.draw.line(surface, tuple(int(c*.35) for c in self.color), self.pos-self.vel*.035, self.pos, 5)
            frame = self.art.frame(int(self.age*10)%4, columns=4)
        image = graphics.render_sprite(frame, 30, self.color)
        if not self.resting:
            image = pygame.transform.rotate(image, self.age*210)
        surface.blit(image, image.get_rect(center=self.pos))
