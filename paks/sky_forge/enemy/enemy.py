"""SkyForge: level-scaled AI, attacks, spawn policy and rewards belong here."""
from dataclasses import dataclass
import math
from system_panic.model import Vec, WIDTH, HEIGHT, Cover, Enemy, normalized, unit
from system_panic.pak_api import EnemyBase
from .tactics import difficulty, spawn_position, pursue
from .physics import move
from .hazards import EmberRing


@dataclass
class Crawler(Enemy):
    age: float = 0.
    timer: float = 0.
    state: str = 'crawl'
    grounded: bool = False
    launch: object = None
    descent_direction: int = 0
    descent_top: float = 0.


class SkyForgeEnemy(EnemyBase):
    def init(self):
        self.creatures = self.load_asset('enemy_sheet.png')

    def sprite(self, world, entity=None):
        if entity is not None and entity.state in ('windup','leap','recover'):
            return self.creatures.frame({'windup':0,'leap':2,'recover':3}[entity.state],columns=4)
        return self.creatures.frame(int((world.time if world else 0)*7+(entity.id if entity else 0))%4,columns=4)

    def sprite_flip_x(self,world,entity):
        return math.cos(entity.angle)<0

    def draw(self,graphics,surface,world,enemy,*,reduced_motion=False):
        image=graphics.component_sprite(world,'enemy',enemy,int(enemy.radius*3.4),rotate=False)
        bounds=image.get_bounding_rect(min_alpha=110)
        offset=enemy.radius-(bounds.bottom-image.get_height()/2)
        surface.blit(image,image.get_rect(center=enemy.pos+Vec(0,offset)))

    def spawn_position(self, world):
        return spawn_position(world)

    def create(self, world, identity, position):
        health = 30 + world.wave * 3
        return Crawler(id=identity, pos=Vec(position), health=health, max_health=health,
                      radius=14, timer=world.rng.uniform(.6, 2), angle=world.rng.uniform(0, math.tau))

    def move_speed(self, world):
        return (65+85*(1-math.exp(-(world.wave-1)/35)))*math.sqrt(difficulty(world))

    def dash_interval(self, world):
        return max(.48, 1.4 / (1 + .04 * (world.wave - 1)) / math.sqrt(difficulty(world)))

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        delta=world.player.pos-enemy.pos
        direction=1 if delta.x>12 else -1 if delta.x< -12 else 0
        descending=False
        if enemy.descent_direction and enemy.pos.y>enemy.descent_top+enemy.radius+8:enemy.descent_direction=0
        if enemy.descent_direction:
            direction,descending=enemy.descent_direction,True
        elif delta.y>50 and enemy.grounded:
            supports=[w for w in world.geometry if type(w) is Cover and w.health>0 and w.blocks_body(enemy)
                      and abs(enemy.pos.y+enemy.radius-w.rect.top)<3 and w.rect.left-enemy.radius<enemy.pos.x<w.rect.right+enemy.radius]
            if supports:
                deck=max(supports,key=lambda w:w.rect.top)
                direction=-1 if enemy.pos.x-deck.rect.left<deck.rect.right-enemy.pos.x else 1
                enemy.descent_direction,enemy.descent_top=direction,deck.rect.top
                descending=True
        if direction and enemy.state=='crawl':enemy.angle=0 if direction>0 else math.pi
        if enemy.state=='crawl':
            enemy.vel.x=direction*self.move_speed(world)
            if enemy.grounded and enemy.timer<=0 and not descending:
                lead=min(.25,max(0,world.wave-3)*.012)
                target=world.player.pos+world.player.vel*lead
                heading=1 if target.x>enemy.pos.x else -1
                enemy.launch=Vec(heading*(155+min(65,world.wave*2)),-405 if target.y<enemy.pos.y-35 else -330)
                enemy.state,enemy.timer,enemy.vel.x='windup',.38,0
                if delta.y< -120:
                    world.projectiles.append(EmberRing(world.safe_position(target,8),self.contact_damage(world)))
        elif enemy.state=='windup':
            enemy.vel.x=0
            if enemy.timer<=0:
                enemy.state,enemy.vel,enemy.grounded='leap',enemy.launch.copy(),False
        elif enemy.state=='recover':
            enemy.vel.x=0
            if enemy.timer<=0:enemy.state,enemy.timer='crawl',self.dash_interval(world)
        enemy.vel.y=min(500,enemy.vel.y+820*dt)
        horizontal,landed=move(world,enemy,dt)
        enemy.grounded=landed
        if any(normal.x for normal in horizontal.normals):
            enemy.vel.x*=-.4 if world.wave>=6 else 0
            if landed:enemy.timer=min(enemy.timer,.1)
        if enemy.state=='leap' and landed:enemy.state,enemy.timer,enemy.vel.x='recover',.48,0

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
