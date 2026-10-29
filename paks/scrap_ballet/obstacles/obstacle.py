"""Level-seeded Pak terrain. Layout generation never consumes gameplay RNG."""
import math
import random
import pygame
from system_panic.model import Cover, Vec, WIDTH, HEIGHT, normalized, circle_rect
from system_panic.pak_api import ObstaclesBase


class Terrain(Cover):
    def __init__(self, rect, kind='solid', phase=0.):
        super().__init__(pygame.Rect(rect),90.,90.)
        self.home=Vec(self.rect.center)
        self.kind,self.phase,self.age=kind,phase,0.
        self.open=False

    def blocks_body(self, body):
        return self.kind=='solid' and not self.open

    def blocks_projectile(self, projectile):
        return self.kind=='solid' and not self.open


class Obstacles(ObstaclesBase):
    def init(self):
        self.art=self.load_asset('obstacles_sheet.png')

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0)*4)%4,columns=4)

    def rng(self, world):
        return random.Random(world.seed*65537+world.wave*8191+601)

    def repair(self, world, walls):
        # Moving/closing terrain must not leave actors embedded in it.
        for body in (world.player,*world.enemies):
            if any(w.health>0 and w.blocks_body(body) and w.overlaps_circle(body.pos,body.radius+1) for w in walls):
                body.pos=world.safe_position(body.pos,body.radius+2,body=body)

    def draw(self, graphics, surface, world, wall):
        color=world.pak('obstacles').color
        if wall.kind=='solid':
            pygame.draw.rect(surface,tuple(int(c*.16) for c in color),wall.rect,border_radius=5)
            pygame.draw.rect(surface,tuple(int(c*(.2 if wall.open else .7)) for c in color),wall.rect,1,border_radius=5)
            image=graphics.render_sprite(self.sprite(world),min(58,max(wall.rect.size)),color)
            surface.blit(image,image.get_rect(center=wall.rect.center))
        else:
            center=Vec(wall.rect.center)
            for r in range(12,max(13,wall.rect.width//2),16):
                pygame.draw.circle(surface,tuple(int(c*.25) for c in color),center,r,1)

    def build(self, world):
        rng=self.rng(world)
        walls=[Terrain((x+rng.randrange(-25,26),y+rng.randrange(-25,26),45,38),phase=rng.random()*6.28)
               for x,y in ((200,125),(700,300),(420,80),(490,350))]
        walls.extend(Terrain((x,140,155,155),'field',rng.random()*6.28) for x in (70,735))
        return walls

    def update(self, world, dt):
        for wall in world.cover:
            wall.age+=dt
            if wall.kind=='solid':
                wall.rect.center=wall.home+Vec(math.sin(wall.age*.4+wall.phase)*28,math.cos(wall.age*.5+wall.phase)*18)
            else:
                center=Vec(wall.rect.center)
                for body in (world.player,*world.enemies):
                    delta=center-body.pos
                    if 15<delta.length()<wall.rect.width:
                        force=normalized(delta)*40+Vec(-delta.y,delta.x).normalize()*35
                        world.move_body(body,force*dt,body.radius)
        self.repair(world,world.cover)

    def draw_floor(self, graphics, surface, world):
        for wall in world.cover:
            if wall.kind=='field':
                p=Vec(wall.rect.center)
                for a in range(0,360,60):
                    direction=Vec(1,0).rotate(a+world.time*25)
                    pygame.draw.line(surface,(85,100,120),p+direction*45,p+direction*65,2)
