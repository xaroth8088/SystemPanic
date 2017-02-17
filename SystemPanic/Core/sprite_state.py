""" Manages the common state for any player, enemy, or missile on the screen
"""
from copy import deepcopy

import pygame

SpriteState = {
    "active": True,
    "sprite": None,
    "pak_specific_state": {},
    "position": {
        "x": 0.0,
        "y": 0.0
    },
    "sprite_size": {
        "width": 0,
        "height": 0
    },
    # Hitbox is relative to top-left corner of sprite
    "hitbox": {
        "x": 0.0,
        "y": 0.0,
        "width": 0.0,
        "height": 0.0
    },
    "facing": {
        "x": 0,
        "y": 0
    },
    "start_time": 0,  # When was this sprite instantiated?
    "wrap_x": False,  # should we wrap around the screen horizontally?
    "wrap_y": False  # should we wrap around the screen vertically?
    # TODO: momentum, rotational momentum, direction facing, etc.
}


def new_sprite():
    return deepcopy(SpriteState)


def do_sprites_collide(sprite_a, sprite_b):
    if sprite_a["active"] is False or sprite_b["active"] is False:
        return False

    hit_a = pygame.Rect(
        sprite_a["hitbox"]["x"] + sprite_a["position"]["x"] - (sprite_a["sprite_size"]["width"] // 2),
        sprite_a["hitbox"]["y"] + sprite_a["position"]["y"] - (sprite_a["sprite_size"]["height"] // 2),
        sprite_a["hitbox"]["width"],
        sprite_a["hitbox"]["height"]
    )

    hit_b = pygame.Rect(
        sprite_b["hitbox"]["x"] + sprite_b["position"]["x"] - (sprite_b["sprite_size"]["width"] // 2),
        sprite_b["hitbox"]["y"] + sprite_b["position"]["y"] - (sprite_b["sprite_size"]["height"] // 2),
        sprite_b["hitbox"]["width"],
        sprite_b["hitbox"]["height"]
    )

    return hit_a.colliderect(hit_b)
