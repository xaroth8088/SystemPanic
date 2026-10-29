"""An inertial paper glider; folding commits to its current input bearing."""
import math
from system_panic.model import Pilot, Vec, Controls, normalized, unit, WIDTH, HEIGHT
from system_panic.pak_api import PilotBase


class PaperPilot(PilotBase):
    controls = 'Arrows / WASD: glide'
    special = 'X: fold into a quick directional dart'

    def init(self):
        self.art = self.load_asset('pilot_sheet.png')
        self.sound = self.load_asset('special.ogg')
        self.heading = Vec(1, 0)
        self.fold_heading = Vec(1, 0)
        self.fold = self.cooldown = 0.
        self.previous_special = False

    def create(self, world, position):
        return Pilot(pos=Vec(position), health=100, max_health=100, radius=11)

    def sprite(self, world, entity=None):
        actor=entity if entity is not None else (world.player if world is not None else None)
        angle=actor.angle if actor is not None else 0.
        facing=int((angle+math.tau/16)%math.tau/(math.tau/8))
        phase=int((world.time if world is not None else 0)*8)%4
        return self.art.frame(phase*8+facing, columns=8, rows=4)

    def sprite_angle(self,world,entity):return 0.

    def sprite_flip_x(self,world,entity):return False


    def on_level_start(self, world):
        self.fold = 0.
        if world.wave > 1:
            world.player.health = min(world.player.max_health, world.player.health+12)
        world.player.invulnerable = max(world.player.invulnerable, 1.5)

    def on_shuffle(self, world, changed):
        self.fold = 0.
        world.player.invulnerable = max(world.player.invulnerable, 1.2)

    def update(self, world, dt, control):
        p = world.player
        self.fold = max(0., self.fold-dt)
        self.cooldown = max(0., self.cooldown-dt)
        direction = Vec(control.x, control.y)
        if direction.length_squared() > 1:
            direction.normalize_ip()
        if direction.length_squared():
            self.heading = direction.normalize()
        if control.special and not self.previous_special and self.cooldown <= 0:
            self.fold_heading = self.heading.copy()
            self.fold, self.cooldown = .2, 2.4
            p.invulnerable = max(p.invulnerable, .22)
            self.sound.play(volume=.45)
            world.burst(p.pos, world.pak('pilot').color, 5)
        self.previous_special = control.special
        desired = self.fold_heading*620 if self.fold > 0 else direction*235
        p.vel = desired if self.fold > 0 else p.vel.lerp(desired, 1-math.exp(-7*dt))
        motion = world.move_body(p, p.vel*dt, p.radius)
        for normal in motion.normals:
            if p.vel.dot(normal) < 0:
                p.vel -= normal*p.vel.dot(normal)
        p.angle = math.atan2(self.heading.y, self.heading.x)

    def take_damage(self, world, damage):
        applied = world.apply_damage(world.player, damage)
        if applied:
            world.player.invulnerable = .85
            world.shake = 4
            world.events.append('hurt')
            world.burst(world.player.pos, (255, 150, 165), 9)
        return applied

    def on_death(self, world):
        world.burst(world.player.pos, world.pak('pilot').color, 35)

    def status(self, world):
        return f'FOLD {self.cooldown:.1f}s' if self.cooldown > 0 else 'FOLD READY'

    def demo_controls(self, world):
        if not world.enemies:
            return Controls()
        p = world.player
        target = min(world.enemies, key=lambda e:e.pos.distance_squared_to(p.pos))
        delta = target.pos-p.pos
        direction = normalized(delta) if delta.length() > 150 else normalized(Vec(-delta.y, delta.x))
        # Moving shutters leave broad routes above/below; choose actual geometry.
        blockers = [w for w in world.geometry if w.health > 0 and w.blocks_body(p)
                    and w.overlaps_segment(p.pos, target.pos)]
        if blockers and delta.length() > 100:
            wall = min(blockers, key=lambda w:Vec(w.rect.center).distance_squared_to(p.pos))
            choices = [y for y in (wall.rect.top-35, wall.rect.bottom+35) if 25 < y < HEIGHT-25]
            if choices:
                route = min(choices, key=lambda y:abs(y-p.pos.y)+.4*abs(y-target.pos.y))
                direction = Vec(normalized(delta).x, 0) if abs(route-p.pos.y) < 10 else Vec(0, 1 if route > p.pos.y else -1)
        if p.pos.x < 40: direction.x = 1
        if p.pos.x > WIDTH-40: direction.x = -1
        if p.pos.y < 40: direction.y = 1
        if p.pos.y > HEIGHT-40: direction.y = -1
        return Controls(int(direction.x>.2)-int(direction.x<-.2), int(direction.y>.2)-int(direction.y<-.2), True, False)
