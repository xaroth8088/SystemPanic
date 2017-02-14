import random

import pygame

from SystemPanic.Core import config


class GameConfiguration:
    def __init__(self):
        self.background = None
        self.enemy = None
        self.enemy_missile = None
        self.player_missile = None
        self.level_generator = None
        self.level_tile = None
        self.music = None
        self.player = None

    def randomize(
            self,
            backgrounds,
            enemies,
            missiles,
            level_generators,
            level_tiles,
            music,
            players
    ):
        self.background = pygame.transform.scale(random.choice(backgrounds),
                                                 (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

        self.level_generator = random.choice(level_generators)()
        self.level_tile = random.choice(level_tiles)()
        self.music = random.choice(music)

        missile = random.choice(missiles)
        self.player_missile = missile["class"]()
        self.player_missile.sprites = missile["sprites"]

        missile = random.choice(missiles)
        self.enemy_missile = missile["class"]()
        self.enemy_missile.sprites = missile["sprites"]

        player = random.choice(players)
        self.player = player["class"]()
        self.player.sprites = player["sprites"]

        enemy = random.choice(enemies)
        self.enemy = enemy["class"]()
        self.enemy.sprites = enemy["sprites"]
