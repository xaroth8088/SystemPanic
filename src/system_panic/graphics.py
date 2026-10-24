"""Rendering helpers and cached AI atlas sprites. Rendering is simulation-free."""
from __future__ import annotations

import math
import pygame

from .resources import asset_root
from .model import WIDTH, HEIGHT, Vec
from .paks import get_catalog

BG = (9, 16, 25)
PANEL = (15, 26, 38)
EDGE = (38, 57, 72)
TEXT = (230, 239, 244)
MUTED = (130, 156, 170)
CYAN = (71, 224, 244)
DIM = (70, 92, 110)


class Graphics:
    def __init__(self, catalog=None):
        self.catalog = catalog if catalog is not None else get_catalog()
        self.fonts = {}
        self.cache = {}
        self.images = {}
        self.title = None
        root = asset_root() / "images"
        if (root / "title.png").is_file():
            self.title = pygame.transform.smoothscale(pygame.image.load(root / "title.png").convert(), (1280, 853))

    def font(self, size, bold=False, mono=False):
        key = (size, bold, mono)
        if key not in self.fonts:
            self.fonts[key] = pygame.font.SysFont("consolas" if mono else "segoeui", size, bold=bold)
        return self.fonts[key]

    def text(self, surface, text, xy, size=20, color=TEXT, bold=False, mono=False, anchor="topleft"):
        image = self.font(size, bold, mono).render(str(text), True, color)
        rect = image.get_rect(**{anchor: xy})
        surface.blit(image, rect)
        return rect

    def wrapped(self, surface, text, xy, width, size=17, color=MUTED, line_height=None):
        line, y = "", xy[1]
        height = line_height or int(size * 1.5)
        for word in text.split():
            candidate = (line + " " + word).strip()
            if self.font(size).size(candidate)[0] > width and line:
                self.text(surface, line, (xy[0], y), size, color)
                y += height
                line = word
            else:
                line = candidate
        if line:
            self.text(surface, line, (xy[0], y), size, color)
            y += height
        return y

    def fit_text(self, surface, text, xy, width, size=20, color=TEXT, bold=False):
        while size > 10 and self.font(size, bold).size(str(text))[0] > width:
            size -= 1
        text = str(text)
        while text and self.font(size, bold).size(text)[0] > width:
            text = text[:-2] + "…"
        return self.text(surface, text, xy, size, color, bold)

    def sprite(self, pak_id, row, size):
        key = (pak_id, row, size)
        if key not in self.cache:
            pak = self.catalog.by_id[pak_id]
            path = pak.sprites[row]
            crop = None
            if path:
                try:
                    if path not in self.images:
                        self.images[path] = pygame.image.load(path).convert_alpha()
                    crop = self.images[path]
                except (pygame.error, OSError):
                    pass
            if crop:
                scale = min(size / crop.get_width(), size / crop.get_height())
                image = pygame.transform.scale(crop, (max(1, int(crop.get_width() * scale)),
                                                       max(1, int(crop.get_height() * scale))))
                tile = pygame.Surface((size, size), pygame.SRCALPHA)
                tile.blit(image, image.get_rect(center=(size / 2, size / 2)))
                self.cache[key] = tile
            else:
                image = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(image, pak.color, (size // 2, size // 2), size // 3)
                self.cache[key] = image
        return self.cache[key]

    def panel(self, surface, rect, fill=PANEL, edge=EDGE, radius=12):
        pygame.draw.rect(surface, fill, rect, border_radius=radius)
        pygame.draw.rect(surface, edge, rect, 1, border_radius=radius)

    def backdrop(self, surface, clock=0, art=True):
        surface.fill(BG)
        if self.title and art:
            surface.blit(self.title, (0, -35))
            wash = pygame.Surface((1280, 800), pygame.SRCALPHA)
            wash.fill((4, 11, 20, 170))
            surface.blit(wash, (0, 0))
            reading_shade = pygame.Surface((410, 800), pygame.SRCALPHA)
            reading_shade.fill((4, 11, 20, 110))
            surface.blit(reading_shade, (0, 0))
        for x in range(0, 1280, 40):
            pygame.draw.line(surface, (15, 30, 41), (x, 0), (x, 800))
        for y in range(0, 800, 40):
            pygame.draw.line(surface, (15, 30, 41), (0, y), (1280, y))

    def draw_world(self, surface, world, reduced_motion=False):
        accent = world.pak("arena").color
        surface.fill((8, 16, 25))
        for x in range(0, WIDTH, 40):
            pygame.draw.line(surface, (15, 28, 40), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 40):
            pygame.draw.line(surface, (15, 28, 40), (0, y), (WIDTH, y))
        if world.pak("arena").draw_arena:
            world.pak("arena").draw_arena(surface)
        pygame.draw.rect(surface, tuple(int(c * .30) for c in accent), (0, 0, WIDTH, HEIGHT), 2)
        for wall in world.cover:
            color = tuple(int(c * .24) for c in accent)
            pygame.draw.rect(surface, (16, 28, 39), wall.rect, border_radius=4)
            pygame.draw.rect(surface, color, wall.rect, 2, border_radius=4)
            if wall.platform:
                pygame.draw.line(surface, accent, wall.rect.topleft, wall.rect.topright, 2)
            else:
                image = self.sprite(world.mix["arena"], 2, min(45, max(wall.rect.size)))
                surface.blit(image, image.get_rect(center=wall.rect.center))
            if wall.health < 36:
                pygame.draw.line(surface, accent, wall.rect.topleft,
                                 (wall.rect.left + wall.rect.width * max(0, wall.health) / 36, wall.rect.top), 2)
        for enemy in world.enemies:
            if enemy.health <= 0:
                continue
            size = int(enemy.radius * 3.4)
            image = self.sprite(world.mix["enemy"], 1, size)
            if world.pak("enemy").rotate_enemy and not reduced_motion:
                image = pygame.transform.rotate(image, -math.degrees(enemy.angle))
            if enemy.elite:
                pygame.draw.circle(surface, world.pak("enemy").color, enemy.pos, int(enemy.radius + 7), 1)
            surface.blit(image, image.get_rect(center=enemy.pos))
            if enemy.health < enemy.max_health:
                bar = pygame.Rect(enemy.pos.x - 16, enemy.pos.y - enemy.radius - 10, 32, 3)
                pygame.draw.rect(surface, (40, 44, 54), bar)
                pygame.draw.rect(surface, world.pak("enemy").color, (bar.x, bar.y, bar.width * max(0, enemy.health) / enemy.max_health, 3))
        for shot in world.projectiles:
            color = world.pak("weapon").color if shot.friendly else (255, 91, 117)
            tail = shot.pos - shot.vel * .022
            pygame.draw.line(surface, tuple(int(c * .45) for c in color), tail, shot.pos, 3)
            if shot.friendly:
                image = self.sprite(world.mix["weapon"], 3, 27 if shot.radius > 4 else 21)
                image = pygame.transform.rotate(image, -math.degrees(math.atan2(shot.vel.y, shot.vel.x)))
                surface.blit(image, image.get_rect(center=shot.pos))
            else:
                pygame.draw.circle(surface, color, shot.pos, 5)
                pygame.draw.circle(surface, (255, 220, 225), shot.pos, 2)
        for beam in world.beams:
            mid = (beam.start + beam.end) / 2 + Vec(0, math.sin(world.time * 60) * 14)
            pygame.draw.lines(surface, world.pak("weapon").color, False, [beam.start, mid, beam.end], 3)
            pygame.draw.lines(surface, (225, 255, 246), False, [beam.start, mid, beam.end], 1)
        p = world.player
        if world.phase != "dead":
            if p.invulnerable > 0:
                pygame.draw.circle(surface, world.pak("pilot").color, p.pos, 20, 1)
            image = self.sprite(world.mix["pilot"], 0, 44)
            if world.pak("pilot").pilot_sprite == "rotate":
                image = pygame.transform.rotate(image, -math.degrees(p.angle) - 90)
            elif world.pak("pilot").pilot_sprite == "face" and math.cos(p.angle) < 0:
                image = pygame.transform.flip(image, True, False)
            if world.phase != "active" or world.transition > 0 or p.invulnerable <= 0 or int(world.time * 12) % 2 or reduced_motion:
                surface.blit(image, image.get_rect(center=p.pos))
            pygame.draw.circle(surface, (240, 255, 255), p.pos + Vec(0, 25), 2)
            pygame.draw.line(surface, world.pak("pilot").color, p.pos + unit_vec(p.angle) * 19,
                             p.pos + unit_vec(p.angle) * 24, 2)
        for particle in world.particles:
            color = tuple(int(c * max(0, particle.life / particle.maximum)) for c in particle.color)
            pygame.draw.circle(surface, color, particle.pos, max(1, int(particle.size * particle.life / particle.maximum)))
        if world.transition > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            if not reduced_motion:
                for i in range(18):
                    y = (i * 47 + int(world.transition * 1100)) % HEIGHT
                    pygame.draw.rect(overlay, (*accent, 60), (0, y, WIDTH, 2 + i % 7))
            else:
                overlay.fill((*accent, 20))
            surface.blit(overlay, (0, 0))


def unit_vec(angle):
    return Vec(math.cos(angle), math.sin(angle))
