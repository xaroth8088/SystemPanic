import random
from copy import deepcopy

import pygame

from SystemPanic.Core import config

GameConfiguration = {
    "background": None,
    "enemy": None,
    "enemy_missile": None,
    "player_missile": None,
    "level_generator": None,
    "level_tile": None,
    "music": None,
    "player": None
}


def new_game_configuration():
    return deepcopy(GameConfiguration)


def get_randomized_config(
        backgrounds,
        enemies,
        missiles,
        level_generators,
        level_tiles,
        music,
        players
):
    new_config = new_game_configuration()

    new_config["background"] = pygame.transform.scale(
        random.choice(backgrounds),
        (
            config.SCREEN_WIDTH,
            config.SCREEN_HEIGHT
        )
    )

    new_config["level_generator"] = random.choice(level_generators)()
    new_config["music"] = random.choice(music)

    level_tile = random.choice(level_tiles)
    new_config["level_tile"] = level_tile["class"]()
    new_config["level_tile"].sprites = level_tile["sprites"]

    missile = random.choice(missiles)
    new_config["player_missile"] = missile["class"]()
    new_config["player_missile"].sprites = missile["sprites"]

    missile = random.choice(missiles)
    new_config["enemy_missile"] = missile["class"]()
    new_config["enemy_missile"].sprites = missile["sprites"]

    player = random.choice(players)
    new_config["player"] = player["class"]()
    new_config["player"].sprites = player["sprites"]

    enemy = random.choice(enemies)
    new_config["enemy"] = enemy["class"]()
    new_config["enemy"].sprites = enemy["sprites"]

    return new_config
