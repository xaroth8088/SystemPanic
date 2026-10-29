"""Burrow Patrol: level-scaled opposition and its local state."""
from dataclasses import dataclass, field
import math
from system_panic.model import Enemy,Vec,WIDTH,HEIGHT,unit,normalized,circle_rect
from system_panic.pak_api import EnemyBase
from .tactics import difficulty,spawn_position,pursue

@dataclass
class BurrowPatrolBody(Enemy):
    age: float = 0.
    timer: float = 1.
    underground: bool = False
    state: str = 'hunt'
    target: object = None

class BurrowPatrolEnemy(EnemyBase):
    def init(self): self.art=self.load_asset("enemy_sheet.png")
    def sprite(self,world,entity=None):
        if entity is not None and entity.state=='burrow':return self.art.frame(1,columns=4)
        return self.art.frame(int((world.time if world else 0)*7+(entity.id if entity else 0))%4,columns=4)

    def spawn_position(self,world):
        return spawn_position(world)

    def create(self,world,identity,position):
        health=30+world.wave*3
        return BurrowPatrolBody(id=identity,pos=Vec(position),health=health,max_health=health,radius=14,
                         angle=world.rng.uniform(0,math.tau),timer=world.rng.uniform(.8,2))

    def move_speed(self,world):
        return (48+110*(1-math.exp(-(world.wave-1)/35)))*difficulty(world)

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        lead=min(.55,max(0,world.wave-3)*.02)
        toward=normalized(world.player.pos+world.player.vel*lead-enemy.pos)
        if enemy.state=='hunt' and enemy.timer<=0:
            enemy.state,enemy.timer='burrow',.9
        elif enemy.state=='burrow' and enemy.timer<=0:
            enemy.pos=world.safe_position(enemy.pos,enemy.radius,body=enemy)
            enemy.target=world.player.pos+world.player.vel*.2
            enemy.state,enemy.timer='rush',.55
            enemy.vel=normalized(enemy.target-enemy.pos)*self.move_speed(world)*2.6
        elif enemy.state=='rush' and enemy.timer<=0:
            enemy.state,enemy.timer='hunt',max(1.2,2.7-world.wave*.025)
        enemy.underground=enemy.state=='burrow'
        if enemy.state=='burrow':
            enemy.vel=toward*self.move_speed(world)*1.35
            enemy.pos+=enemy.vel*dt
            enemy.pos.x=max(16,min(WIDTH-16,enemy.pos.x))
            enemy.pos.y=max(16,min(HEIGHT-16,enemy.pos.y))
        elif enemy.state=='rush':
            motion=world.move_body(enemy,enemy.vel*dt,enemy.radius)
            if motion.normals:enemy.state,enemy.timer='hunt',1.4
        elif enemy.state=='hunt':
            pursue(world,enemy,toward,self.move_speed(world),dt,avoid=world.wave>=4)
        else:enemy.vel=Vec()
        enemy.angle=math.atan2(toward.y,toward.x)

    def sprite_angle(self,world,entity):return -math.degrees(entity.angle)

    def take_damage(self, world, enemy, damage):
        return world.apply_damage(enemy,damage*(.65 if enemy.underground else 1.))

    def contact_damage(self,world):
        return (13+.6*(world.wave-1)**.7)*difficulty(world)

    def on_contact(self,world,enemy,dt):
        if enemy.state!='burrow':world.hit_player(self.contact_damage(world))

    def on_level_complete(self,world):
        world.score+=250*world.wave

    def on_death(self,world,enemy):
        world.score+=100
        world.burst(enemy.pos,world.pak("enemy").color,9)
        world.events.append("impact")
