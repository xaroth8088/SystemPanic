import itertools

import pygame

from SystemPanic.Core.draw_util import draw_text, draw_sprite

DYING_TIME = 1.0


def draw_dying(game_surface, game_state):
    # Add the background
    game_surface.blit(
        game_state["active_config"]["background"],
        [0, 0]
    )

    # Add the sprites (each is drawn atop the previous)
    for sprite_data in itertools.chain(
            game_state["walls"],
            game_state["enemies"],
            game_state["player_missiles"],
            game_state["enemy_missiles"]
    ):
        if sprite_data["active"] is True:
            draw_sprite(game_surface, sprite_data, game_state["garbled"])

    if "dying_timer" not in game_state["mode_specific"]:
        return

    # Add the "score", etc.
    draw_text(game_surface, "OH NOES!", (8, 4), game_state["garbled"])
    draw_text(game_surface, "YOU DIED", (125, 4), game_state["garbled"])
    draw_text(game_surface, "OH NOES!", (240, 4), game_state["garbled"])

    sprite_data = game_state["players"][0]

    # Draw a spinning player
    time_ratio = game_state["mode_specific"]["dying_timer"] / DYING_TIME
    num_spins = 10.5
    angle = (
        360.0 * num_spins * time_ratio
    )

    scale = 1.25 * time_ratio
    if scale < 0:
        scale = 0

    # Get us to the size we were when we died...
    dying_surface = pygame.transform.scale(
        sprite_data["sprite"]["image"],
        (
            sprite_data["sprite_size"]["width"],
            sprite_data["sprite_size"]["height"]
        )
    )

    # Then, shrink down and spin
    dying_surface = pygame.transform.rotozoom(
        dying_surface,
        angle,
        scale
    )

    # Draw it!
    game_surface.blit(
        dying_surface,
        [
            sprite_data["position"]["x"] - (dying_surface.get_width() // 2),
            sprite_data["position"]["y"] - (dying_surface.get_height() // 2)
        ],
    )


def advance_dying(paks, game_state, time_since_start, delta_t):
    from SystemPanic.Core.game_state import change_mode, GAME_MODES, start_new_life

    if "dying_timer" not in game_state["mode_specific"]:
        # This means this is the first time we've been called
        game_state["mode_specific"]["dying_timer"] = DYING_TIME
    else:
        game_state["mode_specific"]["dying_timer"] -= delta_t

    if game_state["mode_specific"]["dying_timer"] <= 0:
        if game_state["lives"] <= 0:
            return change_mode(game_state, GAME_MODES.GAME_OVER)

        return start_new_life(game_state)

    return game_state
