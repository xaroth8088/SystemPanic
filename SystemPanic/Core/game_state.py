from copy import deepcopy
from random import randint

import pygame

from SystemPanic.Core.game_configuration import new_game_configuration
from SystemPanic.Core.sprite_state import do_sprites_collide, new_sprite
from SystemPanic.Core import config

GameState = {
    "active_config": new_game_configuration(),
    "player": new_sprite(),
    "enemies": [],
    "player_missiles": [],
    "enemy_missiles": [],
    "walls": [],
    "level_width": 0,
    "lives": 3,
    "score": 0,
    "level": 0
}


def new_game_state():
    return deepcopy(GameState)


def next_level(game_state):
    game_state["level"] += 1
    game_state["player_missiles"] = []
    game_state["enemy_missiles"] = []

    # Init the level

    # Generate the level
    walls = game_state["active_config"]["level_generator"].generate_walls()

    # Convert the generated walls into sprites

    # Get the width / height for the level
    num_rows = len(walls)
    num_columns = 0
    for y in range(0, num_rows):
        if len(walls[y]) > num_columns:
            num_columns = len(walls[y])

    height = config.SCREEN_HEIGHT // num_rows
    width = config.SCREEN_WIDTH // num_columns

    game_state["walls"] = []
    for y in range(0, num_rows):
        for x in range(0, len(walls[y])):
            if walls[y][x] is True:
                wall = new_sprite()
                wall["position"] = {
                    "x": (x + 0.5) * width,
                    "y": (y + 0.5) * height
                }
                wall["sprite_size"] = {
                    "width": width,
                    "height": height
                }
                wall["hitbox"] = {
                    "x": 0,
                    "y": 0,
                    "width": width,
                    "height": height
                }
                # TODO: decide which sprite to grab based on the walls around this one
                # TODO: this will need to be re-configured whenever we change the level up
                wall["sprite"] = game_state["active_config"]["level_tile"].get_center()
                game_state["walls"].append(wall)

    # Position the player
    game_state["player"]["position"] = {
        "x": randint(0, 800),
        "y": randint(0, 640)
    }

    # Init the enemies
    game_state["enemies"] = [new_sprite() for _ in range(0, game_state["level"])]

    # Position the enemies
    # TODO: account for the level, the player's position, and other enemies' positions
    for enemy in game_state["enemies"]:
        enemy["position"] = {
            "x": randint(0, 800),
            "y": randint(0, 640)
        }

        # Set a default sprite for the enemies, since advance() won't yet have been called for them
        enemy["sprite"] = pygame.Surface((1, 1))

    return game_state


def reconfigure(game_state, new_config):
    # Update our active config
    old_config = deepcopy(game_state["active_config"])
    game_state["active_config"] = new_config

    if old_config is not None:
        # reset pak-specific states where needed
        if old_config["player"].__class__ != new_config["player"].__class__:
            game_state["player"]["pak_specific_state"] = {}

        if old_config["enemy"].__class__ != new_config["enemy"].__class__:
            for enemy in game_state["enemies"]:
                enemy["pak_specific_state"] = {}

        if old_config["player_missile"].__class__ != new_config["player_missile"].__class__:
            for missile in game_state["player_missiles"]:
                missile["pak_specific_state"] = {}

        if old_config["enemy_missile"].__class__ != new_config["enemy_missile"].__class__:
            for missile in game_state["enemy_missiles"]:
                missile["pak_specific_state"] = {}

    return game_state


def advance(game_state, time_since_start, delta_t, pressed_buttons):
    """
    The game engine will call this once per frame
    :param time_since_start: The time in seconds since the game started (useful for animating)
    :param delta_t: The time in seconds since the last time we were called
    :param pressed_buttons: A dict of the controls that are currently active.  Includes:
        "up", "down", "left", "right", "fire"
    :return: whether the game should continue
    """
    all_states = {
        "player": game_state["player"],
        "enemies": game_state["enemies"]
    }

    # Advance the player, including spawning new player missiles
    new_missiles = []
    game_state["player"]["previous_position"] = game_state["player"]["position"].copy()
    game_state["player"] = game_state["active_config"]["player"].advance(
        game_state["player"],
        all_states,
        time_since_start,
        delta_t,
        pressed_buttons,
        new_missiles
    )

    for missile in new_missiles:
        game_state["player_missiles"].append(new_missile(missile, time_since_start))

    # Advance the enemies, including spawning new enemy missiles
    new_missiles = []
    for enemy in game_state["enemies"]:
        enemy["previous_position"] = enemy["position"].copy()
        game_state["active_config"]["enemy"].advance(enemy, all_states, time_since_start, delta_t, new_missiles)

    for missile in new_missiles:
        game_state["enemy_missiles"].append(new_missile(missile, time_since_start))

    # Advance all player missiles
    for missile in game_state["player_missiles"]:
        missile["previous_position"] = missile["position"].copy()
        game_state["active_config"]["player_missile"].advance(missile, all_states, time_since_start, delta_t, "enemy")

    # Advance all enemy missiles
    for missile in game_state["enemy_missiles"]:
        missile["previous_position"] = missile["position"].copy()
        game_state["active_config"]["enemy_missile"].advance(missile, all_states, time_since_start, delta_t, "player")

    game_state = check_player_to_enemy_collisions(game_state)
    game_state = check_player_to_enemy_missile_collisions(game_state)
    game_state = check_enemy_to_player_missile_collisions(game_state)
    game_state = check_level_collisions(game_state)

    # Prune dead missiles
    game_state["player_missiles"] = [missile for missile in game_state["player_missiles"] if missile["active"] is True]
    game_state["enemy_missiles"] = [missile for missile in game_state["enemy_missiles"] if missile["active"] is True]

    # TODO: player dying logic & animation
    if game_state["player"]["active"] is False:
        game_state["lives"] -= 1
        game_state["player"]["active"] = True
        # TODO: Check for end-of-game state, game over screen, new game screen

    # Prune dead enemies
    game_state["enemies"] = [enemy for enemy in game_state["enemies"] if enemy["active"] is True]

    # Should we start a new level?
    if len(game_state["enemies"]) == 0:
        game_state = next_level(game_state)
        # TODO: inter-level screen

    return game_state


def check_player_to_enemy_collisions(game_state):
    for enemy in game_state["enemies"]:
        if do_sprites_collide(game_state["player"], enemy):
            game_state["active_config"]["player"].collided_with_enemy(game_state["player"], enemy)
            game_state["active_config"]["enemy"].collided_with_player(enemy, game_state["player"])

    return game_state


def check_player_to_enemy_missile_collisions(game_state):
    for missile in game_state["enemy_missiles"]:
        if do_sprites_collide(game_state["player"], missile):
            game_state["active_config"]["player"].collided_with_enemy_missile(game_state["player"], missile)
            game_state["active_config"]["enemy_missile"].collided_with_player(missile, game_state["player"])

    return game_state


def check_enemy_to_player_missile_collisions(game_state):
    for enemy in game_state["enemies"]:
        for missile in game_state["player_missiles"]:
            if enemy["active"] is True and missile["active"] is True:
                if do_sprites_collide(enemy, missile):
                    game_state["score"] += 1
                    game_state["active_config"]["enemy"].collided_with_player_missile(enemy, missile)
                    game_state["active_config"]["player_missile"].collided_with_enemy(missile, enemy)

    return game_state


def check_level_collisions(game_state):
    for wall in game_state["walls"]:
        if wall["active"] is True:
            # Player
            if do_sprites_collide(wall, game_state["player"]):
                game_state["player"] = game_state["active_config"]["player"].collided_with_level(
                    game_state["player"],
                    game_state["player"]["previous_position"]
                )

            # Enemy
            for enemy in game_state["enemies"]:
                if do_sprites_collide(wall, enemy):
                    game_state["active_config"]["enemy"].collided_with_level(
                        enemy,
                        enemy["previous_position"]
                    )

            # Player Missiles
            for missile in game_state["player_missiles"]:
                if do_sprites_collide(wall, missile):
                    game_state["active_config"]["player_missile"].collided_with_level(
                        missile,
                        missile["previous_position"]
                    )

            # Enemy Missiles
            for missile in game_state["enemy_missiles"]:
                if do_sprites_collide(wall, missile):
                    game_state["active_config"]["enemy_missile"].collided_with_level(
                        missile,
                        missile["previous_position"]
                    )

    return game_state


def new_missile(missile_data, time_since_start):
    missile = new_sprite()
    missile["start_time"] = time_since_start
    missile["direction"] = missile_data["direction"]
    missile["position"] = missile_data["position"]

    if missile["direction"]["x"] == 0 and missile["direction"]["y"] == 0:
        missile["direction"] = {
            "x": 0,
            "y": 0
        }
    else:
        dir_vector = pygame.math.Vector2(missile["direction"]["x"], missile["direction"]["y"]).normalize()
        missile["direction"] = {
            "x": dir_vector.x,
            "y": dir_vector.y
        }

    return missile
