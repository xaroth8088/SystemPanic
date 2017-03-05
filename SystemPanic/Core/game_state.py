from copy import deepcopy
from random import randint
from enum import Enum
import itertools

import pygame

from SystemPanic.Core.game_configuration import new_game_configuration
from SystemPanic.Core.sprite_state import new_sprite, do_sprites_collide
from SystemPanic.Core import config
from SystemPanic.Core.game_configuration import get_randomized_config
from SystemPanic.Core.Screens.title import advance_title_screen
from SystemPanic.Core.Screens.in_game import advance_in_game
from SystemPanic.Core.Screens.game_over import advance_game_over
from SystemPanic.Core.Screens.ready import advance_ready
from SystemPanic.Core.Screens.level_complete import advance_level_complete



# TODO: should this be something we can set in options?  Or on game start or something?
RANDOMIZE_CONFIGURATION_TIME = 5.0  # in seconds

GAME_MODES = Enum(
    "GAME_MODES",
    "TITLE_SCREEN READY IN_GAME DYING LEVEL_COMPLETE GAME_OVER"
)

GameState = {
    "mode_specific": {},
    "active_config": new_game_configuration(),
    "players": [new_sprite()],
    "enemies": [],
    "player_missiles": [],
    "enemy_missiles": [],
    "walls": [],
    "level_width": 0,
    "lives": 3,
    "score": 0,
    "level": 0,
    "game_mode": GAME_MODES.TITLE_SCREEN,
    "last_randomize_time": 0,
    "garbling_timer": 0,
    "garbled": False,

    "pressed_buttons": {}
    # A dict of the controls that are currently active.  Includes:
    #    "up", "down", "left", "right", "fire"
}


def new_game_state(paks, now):
    return randomize_config(deepcopy(GameState), paks, now)


def next_level(game_state):
    game_state["level"] += 1

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

    height = config.GAME_SURFACE_HEIGHT // num_rows
    width = config.GAME_SURFACE_WIDTH // num_columns

    level_tiles = game_state["active_config"]["level_tile"]
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
                # TODO: decide which sprite to grab based on the walls around this one
                # TODO: this will need to be re-configured whenever we change the level up
                wall["sprite"] = level_tiles["get_center"](
                    level_tiles["sprites"]
                )
                game_state["walls"].append(wall)

    # Init the enemies
    game_state["enemies"] = [new_sprite() for _ in range(0, game_state["level"])]

    # Start a new life
    game_state = start_new_life(game_state)

    return game_state


def start_new_life(game_state):
    # Ensure the player is active
    game_state["players"][0]["active"] = True

    # Clear existing missiles
    game_state["player_missiles"] = []
    game_state["enemy_missiles"] = []

    # Start by positioning the enemies and the player off-screen, so that we can safely re-position them on-screen
    for enemy in game_state["enemies"]:
        enemy["position"] = {
            "x": -9999,
            "y": -9999
        }
    game_state["players"][0]["position"] = {
        "x": -9999,
        "y": -9999
    }

    # Advance the sprites one frame so that they can set their sprites to start with, but
    # don't advance their positions (since we're not checking for collisions, and don't want them stuck in the walls)
    # Similarly, ignore requests to fire new missiles
    for key in ["players", "enemies"]:
        for index in range(0, len(game_state[key])):
            game_state[key][index]["previous_position"] = game_state[key][index]["position"].copy()
            game_state = game_state["active_config"][key]["advance"](
                game_state["active_config"][key]["sprites"],
                (key, index),
                game_state,
                0,
                0,
                []
            )
            game_state[key][index]["position"] = game_state[key][index]["previous_position"].copy()

    # Position the enemies
    game_state["enemies"] = list(map(
        (lambda enemy: position_sprite_safely(game_state, enemy)),
        game_state["enemies"]
    ))

    # Position the player
    game_state["players"][0] = position_sprite_safely(game_state, game_state["players"][0])

    # put us into the 'ready' screen
    return change_mode(game_state, GAME_MODES.READY)


def position_sprite_safely(game_state, sprite):
    # TODO: prevent infinite loops here
    # TODO: Ensure none of the sprites wind up inaccessible from the others
    while True:
        sprite["position"] = {
            "x": randint(0, config.GAME_SURFACE_WIDTH),
            "y": randint(0, config.GAME_SURFACE_HEIGHT)
        }

        if does_sprite_collide_with_list_of_sprites(
                itertools.chain(
                    game_state["walls"],
                    game_state["enemies"],
                    game_state["players"]
                ),
                sprite
        ):
            continue

        return sprite


def does_sprite_collide_with_list_of_sprites(sprite_list, sprite_to_check):
    for sprite in sprite_list:
        if sprite == sprite_to_check:
            continue

        if do_sprites_collide(sprite, sprite_to_check):
            return True

    return False


def reconfigure(game_state, new_config):
    # Update our active config
    old_config = deepcopy(game_state["active_config"])
    game_state["active_config"] = new_config

    if old_config is not None:
        # reset pak-specific states
        for key in ["players", "enemies", "player_missiles", "enemy_missiles"]:
            if old_config[key] != new_config[key]:
                for index in range(0, len(game_state[key])):
                    game_state[key][index]["pak_specific_state"] = {}

    return game_state


def advance(paks, game_state, time_since_start, delta_t, pressed_buttons):
    """
    The game engine will call this once per frame
    :param time_since_start: The time in seconds since the game started (useful for animating)
    :param delta_t: The time in seconds since the last time we were called
    :param pressed_buttons: A dict of the controls that are currently active.  Includes:
        "up", "down", "left", "right", "fire"
    :return: whether the game should continue
    """
    # Prep the frame
    game_state["pressed_buttons"] = pressed_buttons

    # Count down on our garble timer, if appropriate
    game_state["garbled"] = False
    if game_state["garbling_timer"] > 0:
        game_state["garbled"] = True
        game_state["garbling_timer"] -= delta_t

    # Decide whether it's time to re-randomize
    if time_since_start - game_state["last_randomize_time"] > RANDOMIZE_CONFIGURATION_TIME:
        game_state = randomize_config(game_state, paks, time_since_start)

    if game_state["game_mode"] is GAME_MODES.READY:
        return advance_ready(paks, game_state, time_since_start, delta_t)
    elif game_state["game_mode"] is GAME_MODES.IN_GAME:
        return advance_in_game(paks, game_state, time_since_start, delta_t)
    elif game_state["game_mode"] is GAME_MODES.TITLE_SCREEN:
        return advance_title_screen(paks, game_state, time_since_start, delta_t)
    elif game_state["game_mode"] is GAME_MODES.GAME_OVER:
        return advance_game_over(paks, game_state, time_since_start, delta_t)
    elif game_state["game_mode"] is GAME_MODES.LEVEL_COMPLETE:
        return advance_level_complete(paks, game_state, time_since_start, delta_t)

    return game_state


def new_missile(missile_data, time_since_start):
    missile = new_sprite()
    missile["start_time"] = time_since_start
    missile["target"] = missile_data["target"]
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


def randomize_config(game_state, paks, now):
    # TODO: Turn this around - start garbling, but let the game continue to be played while it does.
    # TODO: Then, once the garble completes, randomize the config
    # TODO: This is partly a change here, partly a change in advance_in_game()

    garble_time = 0.5

    game_state["last_randomize_time"] = now + garble_time
    game_state["garbling_timer"] = garble_time

    return reconfigure(
        game_state,
        get_randomized_config(
            paks["backgrounds"],
            paks["enemies"],
            paks["missiles"],
            paks["level_generators"],
            paks["level_tiles"],
            paks["music"],
            paks["players"]
        )
    )


def change_mode(game_state, game_mode):
    game_state["mode_specific"] = {}
    game_state["game_mode"] = game_mode
    return game_state
