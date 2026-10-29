"""Ice eels accumulate momentum and bank away from walls instead of snapping."""
from dataclasses import dataclass
import math
from system_panic.model import Enemy, Vec, WIDTH, HEIGHT, normalized
from system_panic.pak_api import EnemyBase


@dataclass
class Eel(Enemy):
    age: float = 0.


class Enemies(EnemyBase):
    def init(self):
        self.art = self.load_asset("enemy_sheet.png")

    def sprite(self, world, entity=None):
        actor=entity
        angle=actor.angle if actor is not None else 0.
        facing=int((angle+math.tau/16)%math.tau/(math.tau/8))
        phase=int((world.time if world is not None else 0)*8)%4
        return self.art.frame(phase*8+facing, columns=8, rows=4)

    def sprite_angle(self,world,entity):return 0.

    def sprite_flip_x(self,world,entity):return False


    def spawn_position(self, world):
        return world.safe_position(Vec(world.rng.uniform(30, WIDTH - 30), world.rng.uniform(30, HEIGHT - 30)),
                                   14, away_from=world.player.pos, clearance=190)

    def create(self, world, identity, position):
        hp = 29 + world.wave * 3.5
        return Eel(id=identity, pos=Vec(position), radius=14, health=hp, max_health=hp)

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        factor = {"relaxed": .7, "standard": 1., "intense": 1.25}[world.prefs.difficulty]
        aim = world.player.pos + world.player.vel * min(.22, world.wave * .015) - enemy.pos
        heading = normalized(aim).rotate(math.sin(enemy.age * 1.8 + enemy.id) * 22)
        for angle in (0, 45, -45, 80, -80, 140):
            candidate = heading.rotate(angle if enemy.id % 2 else -angle)
            probe = enemy.pos + candidate * 55
            if not any(w.health > 0 and w.blocks_body(enemy) and w.overlaps_circle(probe, enemy.radius + 3) for w in world.geometry):
                heading = candidate
                break
        speed = (68 + 75 * (1 - math.exp(-world.wave / 30))) * factor ** .5
        desired = heading * speed
        enemy.vel += (desired - enemy.vel) * min(1., dt * 1.7)
        motion = world.move_body(enemy, enemy.vel * dt, enemy.radius)
        for normal in motion.normals:
            if enemy.vel.dot(normal) < 0:
                enemy.vel -= 1.8 * enemy.vel.dot(normal) * normal
        if enemy.vel.length_squared() > 1:
            enemy.angle = math.atan2(enemy.vel.y, enemy.vel.x)

    def on_contact(self, world, enemy, dt):
        factor = {"relaxed": .7, "standard": 1., "intense": 1.25}[world.prefs.difficulty]
        world.hit_player((12 + .65 * world.wave ** .7) * factor)

    def take_damage(self, world, enemy, damage):
        amount = world.apply_damage(enemy, damage)
        if amount:
            world.burst(enemy.pos, (188, 238, 255), 3)
        return amount

    def on_death(self, world, enemy):
        world.score += 100
        world.burst(enemy.pos, (188, 238, 255), 10)
        world.events.append("impact")

    def on_level_complete(self, world):
        world.score += world.wave * 250
