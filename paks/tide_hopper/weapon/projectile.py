"""A harpoon catches, reels and finishes a target; no host grapple rules."""
import math
import pygame
from system_panic.model import Vec,WIDTH,HEIGHT,normalized,circle_rect
from system_panic.pak_api import ProjectileBase

class Harpoon(ProjectileBase):
    def __init__(self,world,weapon,direction):
        super().__init__(world.player.pos+direction*20,direction*650,5)
        self.weapon=weapon
        self.target=None
        self.returning=False
        self.remaining=3.
        self.power=world.powerups_collected
        self.flung=False
        self.tension=0.
        self.blocked=0.
        self.hit_ids=set()
    def update(self,world,dt):
        self.remaining-=dt
        if self.remaining<=0:
            self.alive=False
            return
        if self.target is not None:
            if self.target.health<=0 or self.target not in world.enemies:
                self.target=None
                self.returning=True
            else:
                if self.flung:
                    self.fly_target(world,dt)
                    return
                self.tension=min(1.,self.tension+dt)
                if not self.weapon.fire_held:
                    self.flung=True
                    self.vel=self.weapon.throw_direction(world,self.target)*(420+200*self.tension+20*self.power)
                    self.remaining=1.8
                    return
                delta=(world.player.pos-self.target.pos)*min(1,dt*(4+.4*self.power))
                motion=world.move_body(self.target,delta,self.target.radius)
                self.blocked=self.blocked+dt if motion.normals else 0.
                if motion.normals:
                    for wall in world.geometry:
                        if wall.health>0 and wall.blocks_body(self.target) and wall.overlaps_circle(self.target.pos,self.target.radius+3):world.hit_cover(wall,80*dt)
                if self.blocked>.45:
                    self.target=None
                    self.returning=True
                    return
                self.pos=self.target.pos.copy()
                if self.pos.distance_to(world.player.pos)<32:
                    world.hit_enemy(self.target,38+8*self.power)
                    self.alive=False
                return
        if self.returning:
            delta=world.player.pos-self.pos
            if delta.length()<20:
                self.alive=False
                return
            self.vel=normalized(delta)*750
        self.pos+=self.vel*dt
        if not (4<self.pos.x<WIDTH-4 and 4<self.pos.y<HEIGHT-4): self.returning=True
        if not self.returning:
            for wall in world.geometry:
                if wall.health>0 and wall.blocks_projectile(self) and wall.overlaps_circle(self.pos, self.radius):
                    world.hit_cover(wall,40)
                    self.returning=True
                    return
            for enemy in world.enemies:
                if enemy.health>0 and enemy.pos.distance_to(self.pos)<enemy.radius+self.radius:
                    world.hit_enemy(enemy,18+4*self.power)
                    self.target=enemy
                    self.remaining=3.
                    return

    def fly_target(self,world,dt):
        target=self.target
        motion=world.move_body(target,self.vel*dt,target.radius)
        target.vel=self.vel.copy()
        self.pos=target.pos.copy()
        impact=32+8*self.power+25*self.tension
        if motion.normals:
            for wall in world.geometry:
                if wall.health>0 and wall.blocks_body(target) and wall.overlaps_circle(target.pos,target.radius+3):world.hit_cover(wall,impact)
            world.hit_enemy(target,impact)
            world.burst(target.pos,world.pak('weapon').color,12)
            self.alive=False
            return
        for enemy in world.enemies:
            if enemy is target or enemy.health<=0 or enemy.id in self.hit_ids:continue
            if enemy.pos.distance_to(target.pos)<enemy.radius+target.radius:
                self.hit_ids.add(enemy.id)
                world.hit_enemy(enemy,impact)
                world.hit_enemy(target,impact)
                world.burst(target.pos,world.pak('weapon').color,14)
                self.alive=False
                return
    def draw(self,graphics,surface,world):
        color=world.pak("weapon").color
        if not self.flung:pygame.draw.line(surface,tuple(int(c*.55) for c in color),world.player.pos,self.pos,2 if self.target is not None else 1)
        if self.target is not None:pygame.draw.circle(surface,color,self.pos,int(self.target.radius+5+self.tension*6),2)
        image=graphics.render_sprite(self.weapon.sprite(world,self),29,color)
        image=pygame.transform.rotate(image,-math.degrees(math.atan2(self.vel.y,self.vel.x)))
        surface.blit(image,image.get_rect(center=self.pos))
        pass
