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
        return random.Random(world.seed*65537+world.wave*8191+812)

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
        return [Terrain((x+rng.randrange(-20,21),y+rng.randrange(-25,26),14,75),phase=rng.random()*6.28)
                for x,y in ((230,70),(690,70),(330,310),(590,310))]

    def take_damage(self, world, obstacle, damage):return 0.

    def update(self, world, dt):
        for wall in world.cover:
            wall.age+=dt
            wall.rect.centerx=round(wall.home.x+45*math.sin(wall.age*.45+wall.phase))
        self.repair(world,world.cover)

    def draw_floor(self, graphics, surface, world):
        for x in range(24,WIDTH,48):
            pygame.draw.line(surface,(29,57,64),(x,20),(x-100,HEIGHT-20),1)
        for wall in world.cover:
            pygame.draw.line(surface,(130,220,225),wall.rect.topleft,wall.rect.bottomleft,2)
