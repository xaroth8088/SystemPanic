from SystemPanic.Core.draw_util import draw_text, get_font_size
from SystemPanic.Core.Screens.in_game import draw_ingame


def draw_ready(game_surface, game_state):
    # Start by doing the same draw as in-game
    draw_ingame(game_surface, game_state)

    # READY?!
    text = "READY?!"
    text_width, text_height = get_font_size(text)
    draw_text(game_surface, text, (160 - text_width // 2, 120 - text_height // 2), game_state["garbled"])


def advance_ready(paks, game_state, time_since_start, delta_t):
    from SystemPanic.Core.game_state import change_mode, GAME_MODES

    if "ready_timer" not in game_state["mode_specific"]:
        # This means this is the first time we've been called
        game_state["mode_specific"]["ready_timer"] = 1.0
    else:
        game_state["mode_specific"]["ready_timer"] -= delta_t

    if game_state["mode_specific"]["ready_timer"] <= 0:
        return change_mode(game_state, GAME_MODES.IN_GAME)

    return game_state
