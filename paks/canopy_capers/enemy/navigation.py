"""Bounded surface routing from public geometry and this enemy's jump physics.

Rects are usable tops only when they really use Cover's rectangle overlap.
Custom shape bounds remain broad phase data and are never invented platforms.
Graph edges are cheap ballistic reach estimates; a chosen jump is sampled against
the actual public body filters/overlap queries before committing to it.
"""
from collections import OrderedDict
from dataclasses import dataclass
import heapq
import math
from system_panic.model import Cover, Enemy, Vec, WIDTH, HEIGHT

GRAVITY = 900.
JUMP = 460.
AIR_SPEED = 250.


@dataclass(frozen=True)
class Surface:
    key: int
    left: float
    right: float
    top: float

    @property
    def center(self):
        return (self.left + self.right) / 2

    def clamp(self, x):
        return max(self.left, min(self.right, x))


@dataclass(frozen=True)
class Leg:
    source: Surface
    target: Surface
    launch_x: float
    land_x: float
    duration: float


def falling_time(feet, velocity, top):
    discriminant = velocity * velocity + 2 * GRAVITY * (top - feet)
    if discriminant < 0:
        return None
    duration = (-velocity + math.sqrt(discriminant)) / GRAVITY
    return duration if duration > .04 else None


class Navigator:
    def __init__(self):
        self.cache = OrderedDict()

    def surfaces(self, world, body):
        floor = Surface(0, 6 + body.radius, WIDTH - 6 - body.radius, HEIGHT)
        result = [floor]
        probe = Enemy(id=body.id, pos=Vec(), vel=Vec(0, 1), radius=body.radius)
        for wall in world.geometry:
            if (wall.health <= 0 or getattr(wall.overlaps_circle, "__func__", None) is not Cover.overlaps_circle
                    or wall.rect.width < body.radius * 1.5 or not body.radius * 2 + 8 < wall.rect.top < HEIGHT - 8):
                continue
            probe.pos = Vec(wall.rect.centerx, wall.rect.top - body.radius - .05)
            if not wall.blocks_body(probe):
                continue
            left = max(floor.left, wall.rect.left + body.radius * .5)
            right = min(floor.right, wall.rect.right - body.radius * .5)
            if left < right:
                result.append(Surface(id(wall), left, right, wall.rect.top))
        # Dense foreign layouts have bounded planning cost. Actual motion still
        # checks every collider; awkward foreign arrangements may remain awkward.
        if len(result) > 17:
            result = result[:1] + sorted(result[1:], key=lambda s: abs(s.top - body.pos.y - body.radius)
                                         + abs(s.center - body.pos.x) * .2)[:16]
        return tuple(result)

    def graph(self, surfaces):
        if surfaces in self.cache:
            self.cache.move_to_end(surfaces)
            return self.cache[surfaces]
        graph = {surface.key: [] for surface in surfaces}
        for source in surfaces:
            for target in surfaces:
                if source.key == target.key:
                    continue
                rise = source.top - target.top
                if rise > JUMP * JUMP / (2 * GRAVITY) - 8:
                    continue
                duration = falling_time(source.top, -JUMP, target.top)
                if duration is None:
                    continue
                launch = source.clamp(target.center)
                landing = target.clamp(launch)
                if abs(landing - launch) > AIR_SPEED * duration - 8:
                    continue
                graph[source.key].append(Leg(source, target, launch, landing, duration))
        self.cache[surfaces] = graph
        while len(self.cache) > 8:
            self.cache.popitem(last=False)
        return graph

    def supporting(self, body, surfaces):
        feet = body.pos.y + body.radius
        near = [s for s in surfaces if abs(feet - s.top) < 4
                and s.left - body.radius * 1.5 <= body.pos.x <= s.right + body.radius * 1.5]
        return min(near, key=lambda s: abs(feet - s.top)) if near else None

    def goal(self, player, surfaces):
        feet = player.pos.y + player.radius
        def cost(surface):
            vertical = abs(surface.top - feet)
            # A surface just below an airborne target is a useful interception
            # point, whereas a roof far above the target is not its footing.
            return vertical * (1.5 if surface.top < feet - 25 else 1.) + abs(surface.clamp(player.pos.x) - player.pos.x)
        return min(surfaces, key=cost)

    def route(self, surfaces, source, goal, position, blocked):
        if source.key == goal.key:
            return None
        graph = self.graph(surfaces)
        frontier = [(0., source.key)]
        distances, previous = {source.key: 0.}, {}
        while frontier:
            cost, key = heapq.heappop(frontier)
            if cost != distances.get(key):
                continue
            if key == goal.key:
                break
            for leg in graph[key]:
                if (leg.source.key, leg.target.key) in blocked:
                    continue
                walking = abs(leg.launch_x - (position.x if key == source.key else leg.source.center)) / 120
                candidate = cost + leg.duration + walking
                if candidate < distances.get(leg.target.key, float("inf")):
                    distances[leg.target.key] = candidate
                    previous[leg.target.key] = leg
                    heapq.heappush(frontier, (candidate, leg.target.key))
        if goal.key not in previous:
            return None
        leg = previous[goal.key]
        while leg.source.key != source.key:
            leg = previous[leg.source.key]
        # Launch immediately from present footing when that real jump is within
        # reach; do not spend the entire leaf lifetime walking to an ideal edge.
        landing = leg.target.clamp(position.x)
        if abs(landing - position.x) <= AIR_SPEED * leg.duration - 8:
            return Leg(leg.source, leg.target, position.x, landing, leg.duration)
        return leg

    def alternatives(self, body, leg):
        yield leg
        for edge, side in ((leg.target.left, -1), (leg.target.right, 1)):
            launch = leg.source.clamp(edge + side * (body.radius + 28))
            landing = leg.target.clamp(edge - side * 10)
            if abs(landing - launch) <= AIR_SPEED * leg.duration - 8:
                yield Leg(leg.source, leg.target, launch, landing, leg.duration)

    def clear_jump(self, world, body, leg, launch_speed=JUMP):
        duration = falling_time(leg.source.top, -launch_speed, leg.target.top)
        if duration is None:
            return False
        vx = (leg.land_x - leg.launch_x) / duration
        if abs(vx) > AIR_SPEED:
            return False
        probe = Enemy(id=body.id, pos=Vec(), vel=Vec(), radius=body.radius)
        samples = max(12, math.ceil(duration * (abs(vx) + launch_speed) / max(5, body.radius * .6)))
        for index in range(1, min(90, samples) + 1):
            t = duration * index / min(90, samples)
            probe.pos = Vec(leg.launch_x + vx * t, leg.source.top - body.radius - launch_speed * t + .5 * GRAVITY * t * t)
            probe.vel = Vec(vx, -launch_speed + GRAVITY * t)
            if not body.radius + 5 <= probe.pos.x <= WIDTH - body.radius - 5 or probe.pos.y < body.radius + 5:
                return False
            for wall in world.geometry:
                if wall.health <= 0 or not wall.blocks_body(probe):
                    continue
                # At exact arrival, strict circle overlap should be false. The
                # tiny tolerance avoids a floating-point tangent rejection.
                if wall.overlaps_circle(probe.pos, max(1, probe.radius - .1)):
                    return False
        return True
