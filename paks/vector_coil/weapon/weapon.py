"""Hold fire and draw a closed tail with the pilot to capture enclosed enemies."""
from system_panic.model import normalized, unit
from system_panic.pak_api import WeaponBase
from .tail import TailImage, area, contains_body, intersection


class VectorCoilWeapon(WeaponBase):
    def init(self):
        self.art = self.load_asset("weapon_sheet.png")
        self.sound = self.load_asset("shot.ogg")
        self._points = []
        self._visual = None

    def sprite(self, world, entity=None):
        return self.art

    def aim(self, world):
        # Compatibility query for authors; capture has no projectile aiming policy.
        intent = world.component("pilot").aim_direction(world)
        return normalized(intent) if intent is not None else unit(world.player.angle)

    def reset(self):
        self._points.clear()
        if self._visual:
            self._visual.points = []
            self._visual.captured = []
            self._visual.flash = 0.
            self._visual.alive = False
        self._visual = None

    def on_level_start(self, world):
        self.reset()

    def on_shuffle(self, world, changed):
        self.reset()

    def deactivate(self, world):
        self.reset()

    def update(self, world, dt, control):
        if not control.fire:
            self._points.clear()
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
            if closed:
                for enemy in tuple(world.enemies):
                    if enemy.health > 0 and contains_body(closed, enemy):
                        world.hit_enemy(enemy, enemy.health)
                self.sound.play(volume=.45)
                self._points = [position]
            else:
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
                while len(self._points) > 2 and sum(a.distance_to(b) for a, b in zip(self._points, self._points[1:])) > 6000:
                    self._points.pop(0)
            if closed:
                self.show(world)
                self._visual.captured = [p.copy() for p in closed]
                self._visual.flash = .5
        self.show(world)

    def show(self, world):
        if self._visual is None or not self._visual.alive:
            self._visual = TailImage()
            world.effects.append(self._visual)
        self._visual.points = [p.copy() for p in self._points]
        self._visual.remaining = max(.05, self._visual.flash)
