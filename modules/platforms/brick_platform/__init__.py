# modules/platforms/brick_platform/__init__.py
# SPRITESHEET_LAYOUT_NOTE: A single tile image (e.g., 32x32px) named tile.png.

import pygame
import os

from modules.platforms import BasePlatform

TILE_SIZE = 32  # Assuming fixed tile size for this module


class Platform(BasePlatform):
    def __init__(self, x, y, image):
        super().__init__(x, y, image)
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))


def load_platform_assets(module_path):
    tile_path = os.path.join(module_path, "tile.png")
    assets = {}
    try:
        tile_image = pygame.image.load(tile_path).convert()
        # Scale if not TILE_SIZE (optional, good for consistency)
        # tile_image = pygame.transform.scale(tile_image, (TILE_SIZE, TILE_SIZE))
        assets["tile_image"] = tile_image
    except pygame.error as e:
        print(f"Error loading brick platform tile: {e}")
        tile_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        tile_image.fill((150, 75, 0))
        assets["tile_image"] = tile_image
    return assets


def create_platforms(screen_width, screen_height, assets):
    tile_image = assets.get("tile_image")
    if not tile_image:  # Fallback if asset loading failed critically
        tile_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        tile_image.fill((150, 75, 0))

    platforms = pygame.sprite.Group()

    # Ground platform
    for i in range(screen_width // TILE_SIZE + 1):
        platforms.add(Platform(i * TILE_SIZE, screen_height - TILE_SIZE, tile_image))

    # Some floating platforms
    level_layout = [
        "               ",
        "               ",
        "               ",
        "   P P P       ",
        "               ",
        "         PP    ",
        "               ",
        "      P        ",
        "P P            ",
    ]
    # Layout is read from bottom up for easier visualization related to screen coords
    for row_idx, row_str in enumerate(reversed(level_layout)):
        y = screen_height - TILE_SIZE * (row_idx + 2)  # +2 to lift above ground
        for col_idx, char_tile in enumerate(row_str):
            if char_tile == "P":
                x = col_idx * TILE_SIZE
                platforms.add(Platform(x, y, tile_image))

    return platforms
