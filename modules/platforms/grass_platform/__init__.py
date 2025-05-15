# modules/platforms/grass_platform/__init__.py
# SPRITESHEET_LAYOUT_NOTE: A single tile image (e.g., 32x32px) named tile.png.

import pygame
import os
from modules.platforms import BasePlatform

TILE_SIZE = 32


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
        assets["tile_image"] = tile_image
    except pygame.error as e:
        print(f"Error loading grass platform tile: {e}")
        tile_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        tile_image.fill((0, 180, 0))
        pygame.draw.rect(tile_image, (100, 50, 20), (0, 0, TILE_SIZE, 10))
        assets["tile_image"] = tile_image
    return assets


def create_platforms(screen_width, screen_height, assets):
    tile_image = assets.get("tile_image")
    if not tile_image:
        tile_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        tile_image.fill((0, 180, 0))
        pygame.draw.rect(tile_image, (100, 50, 20), (0, 0, TILE_SIZE, 10))

    platforms = pygame.sprite.Group()

    for i in range(screen_width // TILE_SIZE + 1):
        platforms.add(Platform(i * TILE_SIZE, screen_height - TILE_SIZE, tile_image))

    level_layout = [
        "                      ",  # Topmost visual row in this text layout
        "   PPP                ",
        "                      ",
        "            PPP       ",
        "                      ",
        "        P      P      ",
        "                      ",
        "  PP           PP     ",
        "                      ",  # Bottommost visual row in this text layout (just above ground)
    ]
    for row_idx, row_str in enumerate(reversed(level_layout)):
        y = screen_height - TILE_SIZE * (row_idx + 2)
        for col_idx, char_tile in enumerate(row_str):
            if char_tile == "P":
                x = col_idx * TILE_SIZE
                # Ensure platforms are within screen bounds, e.g. for wider levels
                if x < screen_width:
                    platforms.add(Platform(x, y, tile_image))
    return platforms
