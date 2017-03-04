import pygame

from SystemPanic.Core.draw_util import draw_text


def draw_game_over_screen(game_surface, game_state):
    # Add the background
    game_surface.blit(
        game_state["active_config"]["background"],
        [0, 0]
    )

    draw_text(game_surface, "GAME OVER", (160, 120))
    draw_text(game_surface, "FINAL SCORE: %s" % (game_state["score"],), (160, 130))
    if game_state["mode_specific"].get("fade_percent") is not None:
        fade_mask = pygame.Surface(game_surface.get_size(), flags=pygame.SRCALPHA)
        alpha = 255 - game_state["mode_specific"]["fade_percent"] * 255.0
        if alpha < 0:
            alpha = 0
        fade_mask.fill((0, 0, 0, alpha))
        game_surface.blit(
            fade_mask,
            [0, 0]
        )


def advance_game_over(paks, game_state, time_since_start, delta_t):
    from SystemPanic.Core.game_state import change_mode, GAME_MODES, new_game_state

    fade_time = 0.5  # seconds to fade out over
    # We want to ensure that the player has released the fire button before advancing to the title screen,
    # since it's likely that they'll die with the fire button pressed.
    if game_state["pressed_buttons"]["fire"] is False:
        game_state["mode_specific"]["fire_released"] = True
    elif game_state["mode_specific"].get("fire_released") is True:
        game_state["mode_specific"]["fade_timer"] = fade_time

    if game_state["mode_specific"].get("fade_timer") is not None:
        game_state["mode_specific"]["fade_timer"] -= delta_t
        game_state["mode_specific"]["fade_percent"] = game_state["mode_specific"]["fade_timer"] / fade_time

        if game_state["mode_specific"]["fade_timer"] <= 0.0:
            game_state = new_game_state(paks, 0)
            return change_mode(game_state, GAME_MODES.TITLE_SCREEN)

    return game_state
