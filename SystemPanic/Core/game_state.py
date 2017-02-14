from random import randint

import pygame

from SystemPanic.Core.enemy_state import EnemyState
from SystemPanic.Core.missile_state import MissileState
from SystemPanic.Core.player_state import PlayerState


class GameState:
    def __init__(self):
        self.active_config = None

        self.player = None
        self.enemies = []
        self.player_missiles = []
        self.enemy_missiles = []
        self.lives = 0
        self.score = 0
        self.level = 0

    def init_new_game(self):
        self.player = PlayerState()

        self.score = 0
        self.level = 0
        self.lives = 3

    def next_level(self):
        self.level += 1
        self.player_missiles = []
        self.enemy_missiles = []

        # Position the player
        self.player.position = {
            "x": randint(0, 800),
            "y": randint(0, 640)
        }

        # Init the enemies
        self.enemies = [EnemyState() for _ in range(0, self.level)]

        # Position the enemies
        # TODO: account for the level, the player's position, and other enemies' positions
        for enemy in self.enemies:
            enemy.position = {
                "x": randint(0, 800),
                "y": randint(0, 640)
            }

            # Set a default sprite for the enemies, since advance() won't yet have been called for them
            enemy.sprite = pygame.Surface((1, 1))

    def reconfigure(self, config):
        # Update our active config
        old_config = self.active_config
        self.active_config = config

        if old_config is not None:
            # reset pak-specific states where needed
            if old_config.player.__class__ != config.player.__class__:
                self.player.reset_pak_specific_states()

            if old_config.enemy.__class__ != config.enemy.__class__:
                for enemy in self.enemies:
                    enemy.reset_pak_specific_states()

            if old_config.player_missile.__class__ != config.player_missile.__class__:
                for missile in self.player_missiles:
                    missile.reset_pak_specific_states()

            if old_config.enemy_missile.__class__ != config.enemy_missile.__class__:
                for missile in self.enemy_missiles:
                    missile.reset_pak_specific_states()

    def advance(self, time_since_start, delta_t, pressed_buttons):
        """
        The game engine will call this once per frame
        :param time_since_start: The time in seconds since the game started (useful for animating)
        :param delta_t: The time in seconds since the last time we were called
        :param pressed_buttons: A dict of the controls that are currently active.  Includes:
            "up", "down", "left", "right", "fire"
        :return: whether the game should continue
        """
        all_states = {
            "player": self.player,
            "enemies": self.enemies
        }

        # Advance the player, including spawning new player missiles
        new_missiles = []
        self.player = self.active_config.player.advance(self.player, all_states, time_since_start, delta_t,
                                                        pressed_buttons, new_missiles)
        for missile in new_missiles:
            self.player_missiles.append(MissileState(missile["direction"], missile["position"], time_since_start))

        # Advance the enemies, including spawning new enemy missiles
        new_missiles = []
        for enemy in self.enemies:
            self.active_config.enemy.advance(enemy, all_states, time_since_start, delta_t, new_missiles)
        for missile in new_missiles:
            self.enemy_missiles.append(MissileState(missile["direction"], missile["position"], time_since_start))

        # Advance all player missiles
        for missile in self.player_missiles:
            self.active_config.player_missile.advance(missile, all_states, time_since_start, delta_t, "enemy")

        # Advance all enemy missiles
        for missile in self.enemy_missiles:
            self.active_config.enemy_missile.advance(missile, all_states, time_since_start, delta_t, "player")

        self.check_player_to_enemy_collisions()
        self.check_player_to_enemy_missile_collisions()
        self.check_enemy_to_player_missile_collisions()
        self.check_player_to_level_collisions()
        self.check_enemy_to_level_collisions()
        self.check_player_missile_to_level_collisions()
        self.check_enemy_missile_to_level_collisions()

        # Prune dead missiles
        self.player_missiles = [missile for missile in self.player_missiles if missile.active is True]
        self.enemy_missiles = [missile for missile in self.enemy_missiles if missile.active is True]

        # TODO: player dying logic & animation
        if self.player.active is False:
            self.lives -= 1
            self.player.active = True
            # TODO: Check for end-of-game state, game over screen, new game screen

        # Prune dead enemies
        self.enemies = [enemy for enemy in self.enemies if enemy.active is True]

        # Should we start a new level?
        if len(self.enemies) == 0:
            self.next_level()
            # TODO: inter-level screen

        return True

    def check_player_to_enemy_collisions(self):
        for enemy in self.enemies:
            if self.player.collides_with_sprite(enemy):
                self.active_config.player.collided_with_enemy(self.player, enemy)
                self.active_config.enemy.collided_with_player(enemy, self.player)

    def check_player_to_enemy_missile_collisions(self):
        for missile in self.enemy_missiles:
            if self.player.collides_with_sprite(missile):
                self.active_config.player.collided_with_enemy_missile(self.player, missile)
                self.active_config.enemy_missile.collided_with_player(missile, self.player)

    def check_enemy_to_player_missile_collisions(self):
        for enemy in self.enemies:
            for missile in self.player_missiles:
                if enemy.active is True and missile.active is True:
                    if enemy.collides_with_sprite(missile):
                        self.score += 1
                        self.active_config.enemy.collided_with_player_missile(enemy, missile)
                        self.active_config.player_missile.collided_with_enemy(missile, enemy)

    def check_player_to_level_collisions(self):
        pass

    def check_enemy_to_level_collisions(self):
        pass

    def check_player_missile_to_level_collisions(self):
        pass

    def check_enemy_missile_to_level_collisions(self):
        pass
