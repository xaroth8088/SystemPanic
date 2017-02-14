""" Manages the common state for any player, enemy, or missile on the screen
"""
import pygame


class SpriteState:
    def __init__(self):
        self.active = True
        self.sprite = None

        self.pak_specific_state = {}

        self.position = {
            "x": 0.0,
            "y": 0.0
        }

        self.sprite_size = {
            "width": 0,
            "height": 0
        }

        self.hitbox = {
            "x": 0.0,
            "y": 0.0,
            "width": 0.0,
            "height": 0.0
        }

        self.facing = {
            "x": 0,
            "y": 0
        }

        self.wrap_x = False  # should we wrap around the screen horizontally?
        self.wrap_y = False  # should we wrap around the screen vertically?
        # TODO: momentum, rotational momentum, direction facing, etc.

    def set_pak_specific_state(self, key, value):
        self.pak_specific_state[key] = value

    def get_pak_specific_state(self, key):
        if key in self.pak_specific_state:
            return self.pak_specific_state[key]

        return None

    def reset_pak_specific_states(self):
        self.pak_specific_state = {}

    def collides_with_sprite(self, sprite_b):
        if self.active is False or sprite_b.active is False:
            return False

        hit_a = pygame.Rect(
            self.hitbox["x"] + self.position["x"],
            self.hitbox["y"] + self.position["y"],
            self.hitbox["width"],
            self.hitbox["height"]
        )

        hit_b = pygame.Rect(
            sprite_b.hitbox["x"] + sprite_b.position["x"],
            sprite_b.hitbox["y"] + sprite_b.position["y"],
            sprite_b.hitbox["width"],
            sprite_b.hitbox["height"]
        )

        return hit_a.colliderect(hit_b)
