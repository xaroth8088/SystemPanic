"""Hold fire and draw a closed tail with the pilot to capture enclosed enemies."""
from system_panic.model import normalized, unit
from system_panic.pak_api import WeaponBase
from .powerup import VectorCoilPowerup
from .geometry import CarvedArea, LiveLine
from .tail import TailImage, area, contains_body, intersection
from . import network


class VectorCoilWeapon(WeaponBase):
    def init(self):
        self.pickup_sound = self.load_asset("pickup.ogg")
        self.art = self.load_asset("weapon_sheet.png")
        self.sound = self.load_asset("shot.ogg")
        self._points = []
        self._visual = None
        self._areas = []
        self._line_hits = {}

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0)*8)%4,columns=4)

    def aim(self, world):
        # Compatibility query for authors; capture has no projectile aiming policy.
        intent = world.component("pilot").aim_direction(world)
        return normalized(intent) if intent is not None else unit(world.player.angle)

    def reset(self, world, clear_areas=True):
        if clear_areas:
            self._areas.clear()
            self._line_hits.clear()
        world.clear_geometry(self)
        self._points.clear()
        if self._visual:
            self._visual.points = []
            self._visual.captured = []
            self._visual.flash = 0.
            self._visual.alive = False
        self._visual = None

    def on_level_start(self, world):
        self.reset(world)

    def on_shuffle(self, world, changed):
        if changed.intersection({"pilot", "obstacles"}):
            self.reset(world, clear_areas=False)
            world.set_geometry(self,self._areas)

    def deactivate(self, world):
        self.reset(world)

    def update(self, world, dt, control):
        for region in self._areas:region.remaining-=dt
        self._areas=[region for region in self._areas if region.remaining>0]
        if not control.fire:
            self._points.clear()
            world.set_geometry(self,self._areas)
            if self._visual:
                self._visual.points = []
            return
        position = world.player.pos.copy()
        if not self._points or position.distance_to(self._points[-1]) > 160:
            self._points = [position]
        elif position.distance_squared_to(self._points[-1]) > .01:
            start = self._points[-1]
            closed = None
            crossings = []
            for index in range(len(self._points) - 2):
                crossing = intersection(start, position, self._points[index], self._points[index + 1])
                if crossing is not None:
                    polygon = [crossing] + self._points[index + 1:]
                    if area(polygon) >= 900:
                        crossings.append((start.distance_squared_to(crossing), polygon))
            if crossings:
                closed = min(crossings, key=lambda item: item[0])[1]
            if closed is None:closed=network.close(self._points,position,self._areas)
            if closed:
                for enemy in tuple(world.enemies):
                    if enemy.health > 0 and contains_body(closed, enemy):
                        world.hit_enemy(enemy, enemy.health)
                self._areas.append(CarvedArea(closed,world.pak("weapon").color,world.player.radius+3))
                world.set_geometry(self,self._areas)
                world.player.pos=world.safe_position(world.player.pos,world.player.radius)
                for enemy in world.enemies:
                    if enemy.health>0:
                        enemy.pos=world.safe_position(enemy.pos,enemy.radius,body=enemy)
                self.sound.play(volume=.45)
                self._points = [world.player.pos.copy()]
            else:
                # First contact with an old outline becomes a new drawing anchor.
                segments=network.edges(self._areas)
                if segments and network.anchor(self._points[0],segments) is None:
                    joined=network.contact(start,position,segments)
                    if joined is not None:self._points=[joined];start=joined
                if len(self._points) > 1:
                    before, after = start - self._points[-2], position - start
                    if abs(before.cross(after)) < .001 and before.dot(after) > 0:
                        self._points[-1] = position
                    else:
                        self._points.append(position)
                else:
                    self._points.append(position)
                self._points = self._points[-512:]
                # A bounded tail still permits a circuit of the whole arena.
                while len(self._points) > 2 and sum(a.distance_to(b) for a, b in zip(self._points, self._points[1:])) > 6000 + 500 * world.powerups_collected:
                    self._points.pop(0)
            if closed:
                self.show(world)
                self._visual.captured = [p.copy() for p in closed]
                self._visual.flash = .5
        self.show(world)

    def show(self, world):
        if self._visual is None or not self._visual.alive:
            self._visual = TailImage(self.art)
            world.effects.append(self._visual)
        self._visual.points = [p.copy() for p in self._points]
        self._visual.remaining = max(.05, self._visual.flash)
        width=2+min(6,world.powerups_collected*.5)
        live=[LiveLine(a,b,self,width) for a,b in zip(self._points,self._points[1:])]
        world.set_geometry(self,self._areas+live)

    def create_powerup(self,world,position):
        return VectorCoilPowerup(position,self.art,world.pak("weapon").color, self.pickup_sound)

    def on_powerup(self,world,count):
        world.burst(world.player.pos,world.pak("weapon").color,12)
