"""SignalRunner: level-scaled AI, attacks, spawn policy and rewards belong here."""
from dataclasses import dataclass
import math
from system_panic.model import Vec, WIDTH, HEIGHT, Enemy, normalized, unit
from system_panic.pak_api import EnemyBase
from .tactics import difficulty, spawn_position, pursue


@dataclass
class Swarm(Enemy):
    age: float = 0.
    timer: float = 0.
    state: str = 'stalk'
    target: object = None


class SignalRunnerEnemy(EnemyBase):
    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        if entity is not None and entity.state in ('windup','charge','recover'):
            return self.creatures.frame({'windup':2,'charge':3,'recover':0}[entity.state],columns=4)
        return self.creatures.frame(int((world.time if world else 0)*7+(entity.id if entity else 0))%4,columns=4)

    def spawn_position(self, world):
        return spawn_position(world)

    def create(self, world, identity, position):
        health = 30 + world.wave * 3
        return Swarm(id=identity, pos=Vec(position), health=health, max_health=health,
                      radius=14, timer=world.rng.uniform(.6, 2), angle=world.rng.uniform(0, math.tau))

    def move_speed(self, world):
        return (48 + 130 * (1 - math.exp(-(world.wave - 1) / 32))) * difficulty(world) * 1.2

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer-=dt
        if enemy.state=='windup':
            enemy.vel=Vec()
            if enemy.timer<=0:
                enemy.state,enemy.timer='charge',.32
                speed=(300+80*(1-math.exp(-(world.wave-1)/25)))*math.sqrt(difficulty(world))
                enemy.vel=normalized(enemy.target-enemy.pos)*speed
        elif enemy.state=='charge':
            motion=world.move_body(enemy,enemy.vel*dt,enemy.radius)
            if enemy.timer<=0 or motion.normals:
                enemy.state,enemy.timer,enemy.vel='recover',.62,Vec()
        elif enemy.state=='recover':
            enemy.vel=Vec()
            if enemy.timer<=0:
                enemy.state,enemy.timer='stalk',1.1+enemy.id%3*.17
        else:
            self.stalk(world,enemy,dt)
            if enemy.timer<=0 and enemy.pos.distance_to(world.player.pos)<260:
                enemy.state,enemy.timer='windup',.42
                enemy.target=world.player.pos+world.player.vel*min(.2,max(0,world.wave-3)*.012)
                enemy.vel=Vec()

    def stalk(self,world,enemy,dt):
        # Later swarms intercept and flank the pilot's path instead of only chasing.
        lead = min(.5, max(0, world.wave - 3) * .018)
        target = world.player.pos + world.player.vel * lead
        direction = normalized(target - enemy.pos)
        flank = min(.35, max(0, world.wave - 5) * .012) * (-1 if enemy.id % 2 else 1)
        direction = direction.rotate_rad(math.sin(enemy.age * 2 + enemy.id) * .35 + flank)
        pursue(world, enemy, direction, self.move_speed(world), dt, avoid=world.wave >= 4)

    def contact_damage(self, world):
        return (13 + .6 * (world.wave - 1) ** .7) * difficulty(world)

    def on_contact(self, world, enemy, dt):
        if enemy.state in ('windup','recover'):return
        world.hit_player(self.contact_damage(world))

    def on_level_complete(self, world):
        world.score += 250 * world.wave

    def take_damage(self, world, enemy, damage):
        applied = world.apply_damage(enemy, damage)
        if applied:
            world.burst(enemy.pos, world.pak("enemy").color, 2)
        return applied

    def on_death(self, world, enemy):
        world.score += 100
        world.burst(enemy.pos, world.pak("enemy").color, 9)
        world.events.append("impact")
