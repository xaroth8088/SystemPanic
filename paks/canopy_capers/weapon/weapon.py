"""Contact weapon: a swept descending foot crossing, never a ranged attack."""
from system_panic.model import Vec
from system_panic.pak_api import WeaponBase, EffectBase
from .powerup import Upgrade


class Weapon(WeaponBase):
    def init(self):
        self.art = self.load_asset("weapon_sheet.png")
        self.sound = self.load_asset("shot.ogg")
        self.chime = self.load_asset("pickup.ogg")
        self.previous = None
        self.previous_tops = {}
        self.previous_enemy_positions = {}
        self.cooldown = 0.
        self.chain = 0
        self.chain_left = 0.

    def sprite(self, world, entity=None):
        return self.art.frame(int((world.time if world else 0) * 8) % 4, columns=4)

    def create_powerup(self, world, position):
        return Upgrade(position, self.art, world.pak("weapon").color, self.chime)

    def on_powerup(self, world, count):
        world.burst(world.player.pos, world.pak("weapon").color, 12)

    def on_level_start(self, world):
        self.previous = None
        self.previous_tops.clear()
        self.previous_enemy_positions.clear()
        self.cooldown = self.chain_left = 0.
        self.chain = 0

    def on_shuffle(self, world, changed):
        self.previous = None
        self.previous_tops.clear()
        self.previous_enemy_positions.clear()

    def update(self, world, dt, control):
        p = world.player
        self.cooldown = max(0., self.cooldown - dt)
        self.chain_left = max(0., self.chain_left - dt)
        if self.chain_left <= 0:
            self.chain = 0
        before = self.previous
        continuous = before is not None and before.distance_to(p.pos) <= max(24., p.vel.length() * dt * 2 + 6)
        if continuous and p.vel.y > 0 and self.cooldown <= 0:
            old_feet, feet = before.y + p.radius, p.pos.y + p.radius
            candidates = []
            for enemy in world.enemies:
                if enemy.health <= 0:
                    continue
                previous_enemy = self.previous_enemy_positions.get(enemy.id)
                if (previous_enemy is None or previous_enemy.distance_to(enemy.pos)
                        > max(24., enemy.vel.length() * dt * 2 + 6)):
                    continue
                top = enemy.pos.y - enemy.radius
                old_top = self.previous_tops.get(enemy.id, top)
                relative_before, relative_now = old_feet - old_top, feet - top
                if relative_before > 3 or relative_now < 0:
                    continue
                travel = relative_now - relative_before
                if travel <= 0:
                    continue
                impact_speed = p.vel.y - enemy.vel.y
                if impact_speed <= 0:
                    continue
                t = max(0., min(1., -relative_before / travel))
                cross_x = before.x + (p.pos.x - before.x) * t
                if abs(cross_x - enemy.pos.x) <= enemy.radius + p.radius * .62:
                    candidates.append((t, enemy, impact_speed))
            if candidates:
                _, enemy, impact_speed = min(candidates, key=lambda item: item[0])
                self.chain = min(6, self.chain + 1)
                self.chain_left = 2.8
                damage = (.18 * impact_speed * (1 + .16 * world.powerups_collected)
                          * (1 + .08 * (self.chain - 1)))
                applied = world.hit_enemy(enemy, damage)
                # A blocked hit still makes physical contact and bounces.
                p.pos.y = min(p.pos.y, enemy.pos.y - enemy.radius - p.radius)
                p.vel.y = -(260 + min(200, impact_speed * .3) + min(70, world.powerups_collected * 7))
                p.invulnerable = max(p.invulnerable, .16)
                self.cooldown = .12
                self.sound.play(volume=.55)
                world.burst(enemy.pos + Vec(0, -enemy.radius), world.pak("weapon").color, 9)
                world.effects.append(StompFlash(enemy.pos + Vec(0, -enemy.radius), world.pak("weapon").color, self.art))
                if applied:
                    world.score += 15 * self.chain
        self.previous = p.pos.copy()
        self.previous_tops = {e.id: e.pos.y - e.radius for e in world.enemies if e.health > 0}
        self.previous_enemy_positions = {e.id: e.pos.copy() for e in world.enemies if e.health > 0}


class StompFlash(EffectBase):
    def __init__(self, position, color, art):
        self.pos, self.color, self.age, self.alive = Vec(position), color, 0., True
        self.art = art

    def update(self, dt):
        self.age += dt
        self.alive = self.age < .22

    def draw(self, graphics, surface, world):
        import pygame
        width = int(12 + self.age * 110)
        pygame.draw.ellipse(surface, self.color, (self.pos.x - width, self.pos.y - 4, width * 2, 8), 2)
        frame = self.art.frame(min(3, int(self.age * 18)), columns=4)
        image = graphics.render_sprite(frame, 27, self.color).copy()
        image.set_alpha(max(0, int(255 * (1 - self.age / .22))))
        surface.blit(image, image.get_rect(midbottom=self.pos))
