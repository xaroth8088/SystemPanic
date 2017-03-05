from SystemPanic.Core.draw_util import draw_text, get_font_size
from SystemPanic.Core.Screens.in_game import draw_ingame


def draw_level_complete(game_surface, game_state):
    # Start by doing the same draw as in-game
    draw_ingame(game_surface, game_state)

    # Complete!
    text = "Level %s Complete!" % (game_state["level"],)
    text_width, text_height = get_font_size(text)
    draw_text(game_surface, text, (160 - text_width // 2, 120 - text_height // 2), game_state["garbled"])


def advance_level_complete(paks, game_state, time_since_start, delta_t):
    from SystemPanic.Core.game_state import next_level

    if "complete_timer" not in game_state["mode_specific"]:
        # This means this is the first time we've been called
        game_state["mode_specific"]["complete_timer"] = 2.0
    else:
        game_state["mode_specific"]["complete_timer"] -= delta_t

    if game_state["mode_specific"]["complete_timer"] <= 0:
        return next_level(game_state)

    return game_state
