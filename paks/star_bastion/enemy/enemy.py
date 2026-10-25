"""Star Bastion: level-scaled opposition and its local state."""
from dataclasses import dataclass, field
import math
from system_panic.model import Enemy,Vec,WIDTH,HEIGHT,unit,normalized,circle_rect
from system_panic.pak_api import EnemyBase
from .tactics import difficulty,spawn_position,pursue
from .bullet import HostileShot

@dataclass
class StarBastionBody(Enemy):
    age: float = 0.
    timer: float = 1.
    anchor: Vec = field(default_factory=Vec)

class StarBastionEnemy(EnemyBase):
    def init(self): self.art=self.load_asset("enemy_sheet.png")
    def sprite(self,world,entity=None): return self.art

    def spawn_position(self,world):
        index=len(world.enemies)
        desired=Vec(70+(index%10)*85+world.rng.uniform(-12,12),55+(index//10%4)*42)
        return world.safe_position(desired,14,away_from=world.player.pos,clearance=160)

    def create(self,world,identity,position):
        health=30+world.wave*3
        return StarBastionBody(id=identity,pos=Vec(position),health=health,max_health=health,radius=14,
                         angle=world.rng.uniform(0,math.tau),timer=world.rng.uniform(.8,2), anchor=Vec(position))

    def move_speed(self,world):
        return (42+90*(1-math.exp(-(world.wave-1)/35)))*difficulty(world)

    def fire_interval(self, world):
        return max(.8,3.1/(1+.035*(world.wave-1))/difficulty(world))

    def advance_enemy(self, world, enemy, dt):
        enemy.age += dt
        enemy.timer -= dt
        speed=self.move_speed(world)
        # A formation sweep gives way to short predictive dives on later levels.
        diving=world.wave>=5 and (enemy.age+enemy.id*.4)%6>4.5
        if diving:
            direction=normalized(world.player.pos+world.player.vel*.25-enemy.pos)
            pursue(world,enemy,direction,speed*1.8,dt,avoid=True)
        else:
            target=enemy.anchor+Vec(math.sin(enemy.age*(.5+world.wave*.006)+enemy.id)*120,
                                    math.sin(enemy.age*.4)*18)
            pursue(world,enemy,normalized(target-enemy.pos),min(speed,(target-enemy.pos).length()*2),dt,avoid=True)
        if enemy.timer<=0:
            enemy.timer=self.fire_interval(world)
            direction=normalized(world.player.pos+world.player.vel*min(.4,world.wave*.02)-enemy.pos)
            self.shoot(world,enemy,direction,125+100*(1-math.exp(-(world.wave-1)/35)))

    def contact_damage(self,world):
        return (13+.6*(world.wave-1)**.7)*difficulty(world)

    def on_contact(self,world,enemy,dt):
        world.hit_player(self.contact_damage(world))

    def on_level_complete(self,world):
        world.score+=250*world.wave

    def on_death(self,world,enemy):
        world.score+=100
        world.burst(enemy.pos,world.pak("enemy").color,9)
        world.events.append("impact")

    def take_damage(self, world, enemy, damage):
        applied=world.apply_damage(enemy,damage)
        if applied: world.burst(enemy.pos,world.pak("enemy").color,2)
        return applied

    def shoot(self,world,enemy,direction,speed):
        damage=(12+.5*(world.wave-1)**.7)*difficulty(world)
        world.projectiles.append(HostileShot(enemy.pos+direction*(enemy.radius+6),direction*speed,damage))
