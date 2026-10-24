"""Rendering helpers and cached AI atlas sprites. Rendering is simulation-free."""
from __future__ import annotations

import math
import pygame

from .resources import asset_root
from .model import WIDTH, HEIGHT, Vec
from .paks import get_catalog
from .pak_assets import ImageAsset, SpriteFrame

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
        self.previews = {}
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

    def render_sprite(self, handle, size, color=CYAN):
        if handle is None:
            tile = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(tile, color, (size // 2, size // 2), size // 3)
            return tile
        image = handle.image if isinstance(handle, SpriteFrame) else handle
        rect = handle.rect if isinstance(handle, SpriteFrame) else None
        key = (image.path, rect, size)
        if key not in self.cache:
            crop = image.surface
            self.images[image.path] = crop
            if rect is not None:
                crop = crop.subsurface(rect)
            scale = min(size / crop.get_width(), size / crop.get_height())
            frame = pygame.transform.scale(crop, (max(1, int(crop.get_width() * scale)), max(1, int(crop.get_height() * scale))))
            tile = pygame.Surface((size, size), pygame.SRCALPHA)
            tile.blit(frame, frame.get_rect(center=(size / 2, size / 2)))
            self.cache[key] = tile
        return self.cache[key]

    def preview(self, pak_id, size):
        pak = self.catalog.by_id[pak_id]
        for channel in pak.components:
            key = (pak_id, channel)
            if key not in self.previews:
                self.previews[key] = pak.create(channel)
            handle = self.previews[key].preview()
            if handle is not None:
                return self.render_sprite(handle, size, pak.color)
        return self.render_sprite(None, size, pak.color)

    def component_sprite(self, world, channel, entity, size, rotate=True):
        part = world.component(channel)
        image = self.render_sprite(part.sprite(world, entity), size, world.pak(channel).color)
        if rotate:
            angle = part.sprite_angle(world, entity)
            if angle:
                image = pygame.transform.rotate(image, angle)
        if part.sprite_flip_x(world, entity):
            image = pygame.transform.flip(image, True, False)
        return image

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

    def draw_obstacle(self, surface, world, wall):
        """Generic box/sprite presentation; no platform or fixed-health policy."""
        accent = world.pak("obstacles").color
        color = tuple(int(c * .24) for c in accent)
        pygame.draw.rect(surface, (16, 28, 39), wall.rect, border_radius=4)
        pygame.draw.rect(surface, color, wall.rect, 2, border_radius=4)
        image = self.component_sprite(world, "obstacles", wall, min(45, max(wall.rect.size)))
        surface.blit(image, image.get_rect(center=wall.rect.center))
        if wall.health < wall.max_health:
            pygame.draw.line(surface, accent, wall.rect.topleft,
                             (wall.rect.left + wall.rect.width * max(0, wall.health) / wall.max_health, wall.rect.top), 2)

    def draw_world(self, surface, world, reduced_motion=False):
        accent = world.pak("obstacles").color
        world.component("background").draw(surface, world)
        pygame.draw.rect(surface, tuple(int(c * .30) for c in accent), (0, 0, WIDTH, HEIGHT), 2)
        for wall in world.cover:
            world.component("obstacles").draw(self, surface, world, wall)
        for enemy in world.enemies:
            if enemy.health <= 0:
                continue
            size = int(enemy.radius * 3.4)
            image = self.component_sprite(world, "enemy", enemy, size, rotate=not reduced_motion)
            surface.blit(image, image.get_rect(center=enemy.pos))
            if enemy.health < enemy.max_health:
                bar = pygame.Rect(enemy.pos.x - 16, enemy.pos.y - enemy.radius - 10, 32, 3)
                pygame.draw.rect(surface, (40, 44, 54), bar)
                pygame.draw.rect(surface, world.pak("enemy").color, (bar.x, bar.y, bar.width * max(0, enemy.health) / enemy.max_health, 3))
        for shot in world.projectiles:
            if shot.alive:
                shot.draw(self, surface, world)
        for effect in world.effects:
            if effect.alive:
                effect.draw(self, surface, world)
        p = world.player
        if world.phase != "dead":
            if p.invulnerable > 0:
                pygame.draw.circle(surface, world.pak("pilot").color, p.pos, 20, 1)
            image = self.component_sprite(world, "pilot", p, 44)
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
