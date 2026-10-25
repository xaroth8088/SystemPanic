"""Space debris, gravitational wells and scheduled crossing comets."""
import math
import random
import pygame
from system_panic.model import Cover, Vec, WIDTH, HEIGHT, normalized
from system_panic.pak_api import ObstaclesBase


class SpaceRock(Cover):
    def __init__(self,rect,rng):
        super().__init__(rect,45,45)
        center=Vec(rect.center)
        self.points=[center+Vec(math.cos(i*math.tau/9)*rect.width,math.sin(i*math.tau/9)*rect.height)*rng.uniform(.35,.5) for i in range(9)]

    def draw(self,graphics,surface,world):
        pygame.draw.polygon(surface,(51,66,89),self.points)
        pygame.draw.polygon(surface,(112,146,172),self.points,2)
        pygame.draw.circle(surface,(24,35,52),self.rect.center,max(3,self.rect.width//6))


class BlackHole(Cover):
    def __init__(self,position):
        self.pos=Vec(position)
        self.influence=210.
        super().__init__(pygame.Rect(self.pos.x-24,self.pos.y-24,48,48),36,36)

    def blocks_body(self,body):return False
    def blocks_projectile(self,projectile):return False
    def damage(self,world,amount):return 0.

    def draw(self,graphics,surface,world):
        pygame.draw.circle(surface,(42,34,67),self.pos,int(self.influence),1)
        pygame.draw.ellipse(surface,(175,118,231),(self.pos.x-38,self.pos.y-16,76,32),3)
        pygame.draw.circle(surface,(7,4,15),self.pos,21)
        pygame.draw.circle(surface,(234,168,111),self.pos,23,2)


class Comet(Cover):
    def __init__(self,position,velocity):
        self.pos,self.vel=Vec(position),Vec(velocity)
        self.age=0.
        self.hits={}
        super().__init__(pygame.Rect(self.pos.x-12,self.pos.y-12,24,24),36,36)

    def blocks_body(self,body):return False
    def damage(self,world,amount):return 0.
    def overlaps_circle(self,position,radius):return self.pos.distance_squared_to(position)<(radius+12)**2

    def draw(self,graphics,surface,world):
        tail=self.pos-normalized(self.vel)*70
        pygame.draw.line(surface,(74,98,175),tail,self.pos,9)
        pygame.draw.line(surface,(119,207,249),tail.lerp(self.pos,.35),self.pos,4)
        pygame.draw.circle(surface,(240,222,174),self.pos,10)
        pygame.draw.circle(surface,(130,187,221),self.pos,13,2)


class VoidDrifterObstacles(ObstaclesBase):
    def init(self):
        self.blocks=self.load_asset("obstacles_sheet.png")
        self.holes=[]
        self.comets=[]
        self._next_comet=0.
        self._rng=random.Random(0)

    def sprite(self,world,entity=None):return self.blocks

    def build(self,world):
        rng=random.Random(f"{world.seed}:void_drifter:obstacles:{world.wave}")
        self._rng=random.Random(f"{world.seed}:void_drifter:comets:{world.wave}")
        sites=((180,95),(760,340),(770,100),(210,350),(460,80),(850,235))
        count=2+min(3,(world.wave-1)//6)
        rocks=[SpaceRock(pygame.Rect(x+rng.randint(-25,25),y+rng.randint(-20,20),rng.randint(26,45),rng.randint(26,45)),rng) for x,y in rng.sample(sites,count)]
        self.holes=[BlackHole((rng.randint(390,570),rng.randint(200,275)))]
        self.comets=[]
        self._next_comet=world.time+3.+rng.random()*2
        return rocks+self.holes

    def update(self,world,dt):
        if world.time>=self._next_comet:
            self._next_comet=world.time+self._rng.uniform(3.5,6)
            side=self._rng.randrange(4)
            if side==0:pos,vel=Vec(-55,self._rng.uniform(40,440)),Vec(self._rng.uniform(200,300),self._rng.uniform(-55,55))
            elif side==1:pos,vel=Vec(WIDTH+55,self._rng.uniform(40,440)),Vec(-self._rng.uniform(200,300),self._rng.uniform(-55,55))
            elif side==2:pos,vel=Vec(self._rng.uniform(80,880),-55),Vec(self._rng.uniform(-70,70),self._rng.uniform(190,260))
            else:pos,vel=Vec(self._rng.uniform(80,880),HEIGHT+55),Vec(self._rng.uniform(-70,70),-self._rng.uniform(190,260))
            comet=Comet(pos,vel)
            self.comets.append(comet)
            world.cover.append(comet)
        objects=[world.player,*world.enemies,*world.projectiles,*world.powerups,*self.comets]
        enemy_ids={id(e) for e in world.enemies}
        for hole in self.holes:
            for obj in objects:
                if hasattr(obj,"alive") and not obj.alive:continue
                delta=hole.pos-obj.pos
                distance=delta.length()
                if .01<distance<hole.influence:
                    direction=delta/distance
                    strength=(1-distance/hole.influence)
                    drift=direction*(15+120*strength)*dt
                    if obj is world.player or id(obj) in enemy_ids:
                        world.move_body(obj,drift,obj.radius,bounds=None)
                    else:obj.pos+=drift
                    obj.vel+=direction*280*strength*dt
                    if distance<23:
                        if obj is world.player:world.hit_player(18*dt)
                        elif id(obj) in enemy_ids:world.hit_enemy(obj,22*dt)
        for comet in tuple(self.comets):
            comet.age+=dt
            comet.pos+=comet.vel*dt
            comet.rect.center=comet.pos
            if comet.age>12 or not (-100<comet.pos.x<WIDTH+100 and -100<comet.pos.y<HEIGHT+100):
                self.comets.remove(comet)
                world.cover=[wall for wall in world.cover if wall is not comet]
                continue
            for body in (world.player,*world.enemies):
                if body.health>0 and comet.overlaps_circle(body.pos,body.radius) and world.time>=comet.hits.get(id(body),-1):
                    comet.hits[id(body)]=world.time+.6
                    if body is world.player:world.hit_player(14)
                    else:world.hit_enemy(body,28)
                    world.move_body(body,normalized(comet.vel)*24,body.radius)

    def draw(self,graphics,surface,world,obstacle):
        graphics.draw_obstacle(surface,world,obstacle)
