import random
from copy import deepcopy

import pygame

from SystemPanic.Core import config

GameConfiguration = {
    "players": None,
    "enemies": None,
    "player_missiles": None,
    "enemy_missiles": None,

    "background": None,
    "level_generator": None,
    "level_tiles": None,
    "music": None,
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
            config.GAME_SURFACE_WIDTH,
            config.GAME_SURFACE_HEIGHT
        )
    )

    new_config["level_generator"] = random.choice(level_generators)()
    new_config["music"] = random.choice(music)
    new_config["level_tile"] = random.choice(level_tiles)

    new_config["players"] = random.choice(players)
    new_config["player_missiles"] = random.choice(missiles)
    new_config["enemies"] = random.choice(enemies)
    new_config["enemy_missiles"] = random.choice(missiles)

    return new_config
