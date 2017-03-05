import itertools

from SystemPanic.Core.draw_util import draw_text, draw_sprite
from SystemPanic.Core.sprite_state import do_sprites_collide


def draw_ingame(game_surface, game_state):
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
            game_state["enemy_missiles"],
            game_state["players"]
    ):
        if sprite_data["active"] is True:
            draw_sprite(game_surface, sprite_data)

    # Add the score, etc.
    draw_text(game_surface, "Score: %s" % (game_state["score"],), (8, 4), game_state["garbled"])
    draw_text(game_surface, "Level: %s" % (game_state["level"],), (125, 4), game_state["garbled"])
    draw_text(game_surface, "Lives: %s" % (game_state["lives"],), (240, 4), game_state["garbled"])


def advance_in_game(paks, game_state, time_since_start, delta_t):
    from SystemPanic.Core.game_state import next_level, change_mode, GAME_MODES, new_missile

    # If we're garbling, then don't advance
    if game_state["garbling_timer"] > 0:
        return game_state

    # Advance the sprites and add new missiles as we go
    new_missiles = []
    for key in ["players", "enemies", "player_missiles", "enemy_missiles"]:
        for index in range(0, len(game_state[key])):
            game_state[key][index]["previous_position"] = game_state[key][index]["position"].copy()
            game_state = game_state["active_config"][key]["advance"](
                game_state["active_config"][key]["sprites"],
                (key, index),
                game_state,
                time_since_start,
                delta_t,
                new_missiles
            )

    # Collision checks
    game_state = check_player_to_enemy_collisions(game_state)
    game_state = check_player_to_enemy_missile_collisions(game_state)
    game_state = check_enemy_to_player_missile_collisions(game_state)
    game_state = check_level_collisions(game_state)

    # Prune dead missiles
    game_state["player_missiles"] = [missile for missile in game_state["player_missiles"] if missile["active"] is True]
    game_state["enemy_missiles"] = [missile for missile in game_state["enemy_missiles"] if missile["active"] is True]

    # Spawn the newly fired missiles
    for missile in new_missiles:
        if missile["target"] == "enemy":
            game_state["player_missiles"].append(new_missile(missile, time_since_start))
        else:
            game_state["enemy_missiles"].append(new_missile(missile, time_since_start))

    # TODO: player dying animation
    if game_state["players"][0]["active"] is False:
        game_state["lives"] -= 1
        if game_state["lives"] <= 0:
            return change_mode(game_state, GAME_MODES.GAME_OVER)

        game_state["players"][0]["active"] = True

    # Prune dead enemies
    game_state["enemies"] = [enemy for enemy in game_state["enemies"] if enemy["active"] is True]

    # Should we start a new level?
    if len(game_state["enemies"]) == 0:
        game_state = next_level(game_state)
        # TODO: inter-level screen

    return game_state


def check_player_to_enemy_collisions(game_state):
    for enemy in game_state["enemies"]:
        if do_sprites_collide(game_state["players"][0], enemy):
            game_state["active_config"]["players"]["collided_with_enemy"](game_state["players"][0], enemy)
            game_state["active_config"]["enemies"]["collided_with_player"](enemy, game_state["players"][0])

    return game_state


def check_player_to_enemy_missile_collisions(game_state):
    for missile in game_state["enemy_missiles"]:
        if do_sprites_collide(game_state["players"][0], missile):
            game_state["active_config"]["players"]["collided_with_enemy_missile"](game_state["players"][0], missile)
            game_state["active_config"]["enemy_missiles"]["collided_with_player"](missile, game_state["players"][0])

    return game_state


def check_enemy_to_player_missile_collisions(game_state):
    for enemy in game_state["enemies"]:
        for missile in game_state["player_missiles"]:
            if enemy["active"] is True and missile["active"] is True:
                if do_sprites_collide(enemy, missile):
                    game_state["score"] += 1
                    game_state["active_config"]["enemies"]["collided_with_player_missile"](enemy, missile)
                    game_state["active_config"]["player_missiles"]["collided_with_enemy"](missile, enemy)

    return game_state


def check_level_collisions(game_state):
    for wall in game_state["walls"]:
        if wall["active"] is True:
            # Player
            if do_sprites_collide(wall, game_state["players"][0]):
                game_state["players"][0] = game_state["active_config"]["players"]["collided_with_level"](
                    game_state["players"][0],
                    game_state["players"][0]["previous_position"]
                )

            # Enemy
            for enemy in game_state["enemies"]:
                if do_sprites_collide(wall, enemy):
                    game_state["active_config"]["enemies"]["collided_with_level"](
                        enemy,
                        enemy["previous_position"]
                    )

            # Player Missiles
            for missile in game_state["player_missiles"]:
                if do_sprites_collide(wall, missile):
                    game_state["active_config"]["player_missiles"]["collided_with_level"](
                        missile,
                        missile["previous_position"]
                    )

            # Enemy Missiles
            for missile in game_state["enemy_missiles"]:
                if do_sprites_collide(wall, missile):
                    game_state["active_config"]["enemy_missiles"]["collided_with_level"](
                        missile,
                        missile["previous_position"]
                    )

    return game_state
