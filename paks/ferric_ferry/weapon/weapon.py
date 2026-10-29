"""Plant two grounded terminals; charge their fixed rail and discharge an armature."""
from system_panic.pak_api import WeaponBase
from system_panic.model import Vec, normalized, WIDTH, HEIGHT
from .rail import Terminal, Conduit, Armature, conducting_path, closest_point, overlaps_path
from .powerup import Upgrade


class FerricWeapon(WeaponBase):
    MIN_SPAN = 48.
    MIN_CHARGE = .22

    def init(self):
        self.art = self.load_asset('weapon_sheet.png')
        self.sound = self.load_asset('shot.ogg')
        self.chime = self.load_asset('pickup.ogg')
        self.previous_fire = False
        self.charge = 0.
        self.terminals = []
        self.conduit = None
        self.armature = None
        self.demo_cycle = 0.

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0)*8)%4, columns=4)

    def maximum_charge(self, world):
        return 1.2+min(1.2, world.powerups_collected*.12)

    def geometry(self, world):
        shapes = self.terminals+([self.conduit] if self.conduit is not None else [])
        world.set_geometry(self, shapes)

    def place(self, world):
        position = world.player.pos.copy()
        if not self.terminals:
            self.terminals.append(Terminal(position, self.art, world.pak('weapon').color))
            self.geometry(world)
            world.burst(position, world.pak('weapon').color, 4)
            return
        if position.distance_to(self.terminals[-1].position) < self.MIN_SPAN:
            # Standing at a planted pole recharges an existing pair. A single
            # pole cannot short itself into a damaging shot.
            return
        if self.armature is not None:
            self.armature.alive = False
            self.armature = None
        self.terminals = (self.terminals+[Terminal(position, self.art, world.pak('weapon').color)])[-2:]
        self.conduit = Conduit(self.terminals[-1].position, self.terminals[0].position,
                               world.pak('weapon').color)
        self.geometry(world)
        world.burst(position, world.pak('weapon').color, 5)

    def update(self, world, dt, control):
        if self.armature is not None and (not self.armature.alive or self.armature not in world.projectiles):
            self.armature = None
        pressed = control.fire and not self.previous_fire
        released = self.previous_fire and not control.fire
        if pressed:
            self.charge = 0.
            self.place(world)
        if self.conduit is not None:
            start, end, blocker = conducting_path(world, self.conduit.start, self.conduit.end, self.conduit, radius=4)
            self.conduit.powered = bool(control.fire)
            self.conduit.live_end = end
            if control.fire:
                self.charge = min(self.maximum_charge(world), self.charge+dt)
                self.conduit.strength = self.charge/self.maximum_charge(world)
                # The fixed conductor is an induction trap for both sides.
                # Attraction moves a body toward actual copper, never toward a
                # target provider or through intervening projectile cover.
                for body in (world.player, *world.enemies):
                    nearest = closest_point(body.pos, start, end)
                    delta = nearest-body.pos
                    distance = delta.length()
                    if (body.health > 0 and 3 < distance < 110
                            and not world.segment_blocked(nearest, body.pos, self.conduit)):
                        force = normalized(delta)*(80*(1-distance/110))
                        world.move_body(body, force*dt, body.radius)
                        body.vel += force*(dt*.5)
                # The held conduit conducts real current now; it is not a
                # preview of a future attack or a player-to-target tether.
                for enemy in world.enemies:
                    if enemy.health > 0 and start.distance_squared_to(end) > .0001 and overlaps_path(enemy, start, end, 4):
                        world.hit_enemy(enemy, (9+self.charge*7+world.powerups_collected)*dt)
            if released:
                if self.charge+1e-9 >= self.MIN_CHARGE and start.distance_to(end) >= 8:
                    if self.armature is not None: self.armature.alive = False
                    self.armature = Armature(start, self.conduit.end, self.charge,
                                             world.powerups_collected, self.art, world.pak('weapon').color)
                    world.projectiles.append(self.armature)
                    self.sound.play(volume=.55)
                    world.burst(start, world.pak('weapon').color, 7)
                self.charge = 0.
                self.conduit.strength = 0.
        self.previous_fire = bool(control.fire)

    def reset(self, world):
        if self.armature is not None: self.armature.alive = False
        self.armature = None
        self.terminals.clear()
        self.conduit = None
        self.charge = 0.
        self.previous_fire = False
        world.clear_geometry(self)

    def on_level_start(self, world):
        self.reset(world)
        self.demo_cycle = world.time

    def on_shuffle(self, world, changed):
        # Planted geometry survives unrelated swaps. The host clears scheduled
        # shots, so flight references cannot resurrect an old discharge. A
        # locked weapon keeps charge and its held-input edge history: a music
        # swap must not manufacture a fresh terminal placement.
        if self.armature is not None: self.armature.alive = False
        self.armature = None
        if self.conduit is not None:
            _, self.conduit.live_end, _ = conducting_path(world, self.conduit.start, self.conduit.end, self.conduit, radius=4)

    def deactivate(self, world):
        self.reset(world)

    def create_powerup(self, world, position):
        return Upgrade(position, self.art, world.pak('weapon').color, self.chime)

    def on_powerup(self, world, count):
        world.burst(world.player.pos, world.pak('weapon').color, 12)

    def demo_controls(self, world, controls):
        # Lay copper within induction reach instead of using a gun's distant
        # orbit. These remain ordinary digital inputs through the pilot's own
        # locomotion; no direct placement or health/resource advantage is used.
        controls.fire = (world.time-self.demo_cycle)%1.6 < .7
        targets = [enemy for enemy in world.enemies if enemy.health > 0]
        if not targets: return controls
        p = world.player
        target = min(targets, key=lambda enemy:enemy.pos.distance_squared_to(p.pos))
        delta = target.pos-p.pos
        toward = normalized(delta)
        direction = toward if delta.length() > 125 else Vec(-toward.y, toward.x)-toward*.2
        if delta.length() < 70: direction = -toward
        blockers = [wall for wall in world.geometry if wall.health > 0 and wall.blocks_body(p)
                    and wall.overlaps_circle(p.pos+normalized(direction)*35, p.radius+3)]
        if blockers:
            wall = min(blockers, key=lambda item:Vec(item.rect.center).distance_squared_to(p.pos))
            side = p.pos-Vec(wall.rect.center)
            direction = Vec(direction.x*.3, 1 if side.y > 0 else -1) if abs(side.x) < abs(side.y) else Vec(1 if side.x > 0 else -1, direction.y*.3)
        if p.pos.x < 40: direction.x = 1
        if p.pos.x > WIDTH-40: direction.x = -1
        if p.pos.y < 40: direction.y = 1
        if p.pos.y > HEIGHT-40: direction.y = -1
        controls.x = int(direction.x>.2)-int(direction.x<-.2)
        controls.y = int(direction.y>.2)-int(direction.y<-.2)
        return controls
