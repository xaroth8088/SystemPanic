from SystemPanic.Core.draw_util import draw_text


def draw_title_screen(game_surface, game_state):
    # Add the background
    game_surface.blit(
        game_state["active_config"]["background"],
        [0, 0]
    )

    draw_text(game_surface, "SYSTEM PANIC!", (160, 120), game_state["garbled"])
    draw_text(game_surface, "PRESS FIRE TO START", (160, 130), game_state["garbled"])


def advance_title_screen(paks, game_state, time_since_start, delta_t):
    from SystemPanic.Core.game_state import next_level, change_mode, GAME_MODES

    # We want to ensure that the player has released the fire button before advancing to the title screen,
    # since it's likely that they'll die with the fire button pressed.
    if game_state["pressed_buttons"]["fire"] is False:
        game_state["mode_specific"]["fire_released"] = True
    elif game_state["mode_specific"].get("fire_released") is True:
        game_state = next_level(game_state)

    return game_state
