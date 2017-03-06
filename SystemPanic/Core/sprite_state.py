""" Manages the common state for any player, enemy, or missile on the screen
"""
from copy import deepcopy

from pygame import Rect

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

    "target": None,
    # One of "enemy" or "player", usually only useful for missiles

    "facing": {
        "x": 0,
        "y": 0
    },
    "start_time": 0,  # When was this sprite instantiated?
    "wrap_x": False,  # should we wrap around the screen horizontally?
    "wrap_y": False,  # should we wrap around the screen vertically?

    "velocity": {
        "x": 0,
        "y": 0
    }
    # TODO: momentum, rotational momentum, direction facing, etc.  Basically other physics state
}


def new_sprite():
    return deepcopy(SpriteState)


def do_sprites_collide(sprite_a, sprite_b):
    if sprite_a["active"] is False or sprite_b["active"] is False:
        return False

    hitbox_x_ratio_a = sprite_a["sprite_size"]["width"] / sprite_a["sprite"]["original size"]["width"]
    hitbox_y_ratio_a = sprite_a["sprite_size"]["height"] / sprite_a["sprite"]["original size"]["height"]

    hitbox_x_ratio_b = sprite_b["sprite_size"]["width"] / sprite_b["sprite"]["original size"]["width"]
    hitbox_y_ratio_b = sprite_b["sprite_size"]["height"] / sprite_b["sprite"]["original size"]["height"]

    hit_a = Rect(
        sprite_a["position"]["x"] - (sprite_a["sprite_size"]["width"] / 2.0) + sprite_a["sprite"]["hitbox"][
            "x"] * hitbox_x_ratio_a,
        sprite_a["position"]["y"] - (sprite_a["sprite_size"]["height"] / 2.0) + sprite_a["sprite"]["hitbox"][
            "y"] * hitbox_y_ratio_a,
        sprite_a["sprite"]["hitbox"]["width"] * hitbox_x_ratio_a,
        sprite_a["sprite"]["hitbox"]["height"] * hitbox_y_ratio_a
    )

    hit_b = Rect(
        sprite_b["position"]["x"] - (sprite_b["sprite_size"]["width"] / 2.0) + sprite_b["sprite"]["hitbox"][
            "x"] * hitbox_x_ratio_b,
        sprite_b["position"]["y"] - (sprite_b["sprite_size"]["height"] / 2.0) + sprite_b["sprite"]["hitbox"][
            "y"] * hitbox_y_ratio_b,
        sprite_b["sprite"]["hitbox"]["width"] * hitbox_x_ratio_b,
        sprite_b["sprite"]["hitbox"]["height"] * hitbox_y_ratio_b
    )

    return hit_a.colliderect(hit_b)
