"""IronCircuit: level-scaled AI, attacks, spawn policy and rewards belong here."""
from dataclasses import dataclass
import math
from system_panic.model import Vec, WIDTH, HEIGHT, Enemy, normalized, unit
from system_panic.pak_api import EnemyBase
from .tactics import difficulty, spawn_position, pursue
from .bullet import HostileShot


@dataclass
class Turret(Enemy):
    age: float = 0.
    timer: float = 0.
    volley: int = 0
    state: str = 'idle'
    target: object = None


class IronCircuitEnemy(EnemyBase):
    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        if entity is not None and entity.state in ('windup','recover'):
            return self.creatures.frame(2 if entity.state=='windup' else 3,columns=4)
        return self.creatures.frame(int((world.time if world else 0)*7+(entity.id if entity else 0))%4,columns=4)

    def sprite_angle(self,world,entity):
        return -math.degrees(entity.angle)-45

    def spawn_position(self, world):
        return spawn_position(world)

    def create(self, world, identity, position):
        health = 30 + world.wave * 3
        return Turret(id=identity, pos=Vec(position), health=health, max_health=health,
                      radius=14, timer=world.rng.uniform(.6, 2), angle=world.rng.uniform(0, math.tau))

    def shot_speed(self, world):
        return (135 + 150 * (1 - math.exp(-(world.wave - 1) / 30))) * math.sqrt(difficulty(world))

    def fire_interval(self, world):
        return max(.65, 2.72 / (1 + .035 * (world.wave - 1)) / difficulty(world))

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        speed = self.shot_speed(world)
        travel = min(.65, enemy.pos.distance_to(world.player.pos) / speed)
        lead = travel * min(.75, max(0, world.wave - 3) * .035)
        toward = normalized(world.player.pos + world.player.vel * lead - enemy.pos)
        if enemy.state=='windup':toward=normalized(enemy.target-enemy.pos)
        if enemy.state!='recover':enemy.angle = math.atan2(toward.y, toward.x)
        if enemy.state=='idle' and enemy.timer<=0:
            enemy.state,enemy.timer='windup',.55
            enemy.target=world.player.pos+world.player.vel*lead
        elif enemy.state=='windup' and enemy.timer<=0:
            direction=normalized(enemy.target-enemy.pos)
            self.shoot(world,enemy,direction,speed)
            enemy.volley+=1
            if world.wave>=8 and enemy.volley%2==0:
                for offset in (-.16,.16):self.shoot(world,enemy,direction.rotate_rad(offset),speed*.9)
            enemy.state,enemy.timer='recover',.7
        elif enemy.state=='recover' and enemy.timer<=0:
            enemy.state,enemy.timer='idle',max(.35,self.fire_interval(world)-1.25)

    def shoot(self, world, enemy, direction, speed):
        damage = (12 + .5 * (world.wave - 1) ** .7) * difficulty(world)
        world.projectiles.append(HostileShot(enemy.pos + direction * (enemy.radius + 6), direction * speed, damage))

    def contact_damage(self, world):
        return (13 + .6 * (world.wave - 1) ** .7) * difficulty(world)

    def on_contact(self, world, enemy, dt):
        world.hit_player(self.contact_damage(world))

    def on_level_complete(self, world):
        world.score += 250 * world.wave

    def take_damage(self, world, enemy, damage):
        multiplier=1.45 if enemy.state=='recover' else .9 if enemy.state=='windup' else .5
        applied = world.apply_damage(enemy, damage*multiplier)
        if applied:
            world.burst(enemy.pos, world.pak("enemy").color, 2)
        return applied

    def on_death(self, world, enemy):
        world.score += 100
        world.burst(enemy.pos, world.pak("enemy").color, 9)
        world.events.append("impact")
