def get_sprite_details():
    """
        Tells the game engine how to slice up your spritesheet.

        Each slice of your spritesheet should be an object that looks like this:
        {
            "image rect": {
                "x": <x offset in pixels, relative to left edge>,
                "y": <y offset in pixels, relative to top edge>,
                "width": <width in pixels>,
                "height": <height in pixels>
            },
            "hitbox": {
                "x": <x offset in pixels, relative to the left edge of this sprite's image>,
                "y": <y offset in pixels, relative to the top edge of this sprite's image>,
                "width": <width in pixels>,
                "height": <height in pixels>
            }
        }

        Slices are grouped into arrays, one per key that you define.  That key is what you'll use to get
        the sprite object later when deciding what to set in the state's "sprite" field.

    :return: A dict, where each key holds an array of the dicts described above.
    """
    return {
        "left": [
            {
                "image rect": {
                    "x": 0,
                    "y": 512,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
            {
                "image rect": {
                    "x": 256,
                    "y": 512,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
            {
                "image rect": {
                    "x": 512,
                    "y": 512,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
            {
                "image rect": {
                    "x": 768,
                    "y": 512,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
        ],
        "right": [
            {
                "image rect": {
                    "x": 0,
                    "y": 768,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
            {
                "image rect": {
                    "x": 256,
                    "y": 768,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
            {
                "image rect": {
                    "x": 512,
                    "y": 768,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
            {
                "image rect": {
                    "x": 768,
                    "y": 768,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
        ],
        "up": [
            {
                "image rect": {
                    "x": 0,
                    "y": 256,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
            {
                "image rect": {
                    "x": 256,
                    "y": 256,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
            {
                "image rect": {
                    "x": 512,
                    "y": 256,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
            {
                "image rect": {
                    "x": 768,
                    "y": 256,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
        ],
        "down": [
            {
                "image rect": {
                    "x": 0,
                    "y": 0,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
            {
                "image rect": {
                    "x": 256,
                    "y": 0,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
            {
                "image rect": {
                    "x": 512,
                    "y": 0,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
            {
                "image rect": {
                    "x": 768,
                    "y": 0,
                    "width": 256,
                    "height": 256
                },
                "hitbox": {
                    "x": 92,
                    "y": 32,
                    "width": 72,
                    "height": 190
                }
            },
        ]
    }


def advance(sprites, path, game_state, time_since_start, delta_t, new_missiles):
    """
    :param sprites: the sprites object constructed from get_sprite_details
    :param path: the (key, index) tuple that describes how to find ourselves in the game_state
        Example:
            key, index = path
            our_state = game_state[key][index]
    :param game_state: the entire game state
    :param time_since_start: time in seconds from game start (useful for animation)
    :param delta_t: time in seconds since we were last called
    :param new_missiles: If you want to fire a new missile, append a dict for each new missile with
        a dict like: {
            "target": <TARGET>,
            "direction": { "x": #, "y": # },
            "position": { "x": #, "y": # }
        }

        ...where <TARGET> is one of "player" or "enemy".

        The direction vector need not be normalized. Note that the missile may choose to override this direction
        once fired!

    :return: the new game_state
    """
    key, index = path
    player_state = game_state[key][index]

    # What size should our sprite be drawn on-screen as?
    player_state["sprite_size"]["width"] = 16
    player_state["sprite_size"]["height"] = 16

    # What's our hitbox rect (relative to the top-left corner of the sprite)?
    player_state["hitbox"] = {
        "x": 11,
        "y": 4,
        "width": 9,
        "height": 24
    }

    # How are we moving?  And what's our sprite?
    player_state["sprite"] = sprites["down"][0]  # "Idle"

    walking_speed = 64.0

    if game_state["pressed_buttons"]["left"] is True:
        player_state["position"]["x"] -= walking_speed * delta_t
        player_state["sprite"] = sprites["left"][int(time_since_start * 8) % 4]
    if game_state["pressed_buttons"]["right"] is True:
        player_state["position"]["x"] += walking_speed * delta_t
        player_state["sprite"] = sprites["right"][int(time_since_start * 8) % 4]
    if game_state["pressed_buttons"]["up"] is True:
        player_state["position"]["y"] -= walking_speed * delta_t
        player_state["sprite"] = sprites["up"][int(time_since_start * 8) % 4]
    if game_state["pressed_buttons"]["down"] is True:
        player_state["position"]["y"] += walking_speed * delta_t
        player_state["sprite"] = sprites["down"][int(time_since_start * 8) % 4]

    # TODO: move this sort of logic into the missile pak - players shouldn't care about this
    if game_state["pressed_buttons"]["fire"] is True:
        # Limit firing to once per 0.5 seconds
        last_fired = player_state["pak_specific_state"].get("last_fired")

        if last_fired is None or time_since_start - last_fired > 0.5:
            new_missiles.append(
                {
                    "target": "enemy",
                    "direction": {"x": 1.0, "y": 0.0},
                    "position": {"x": player_state["position"]["x"], "y": player_state["position"]["y"]}
                }
            )
            player_state["pak_specific_state"]["last_fired"] = time_since_start

    # How do we interact with the borders of the screen?
    player_state["wrap_x"] = True
    player_state["wrap_y"] = True

    # Return the new state
    return game_state


def collided_with_enemy(player_state, enemy_state):
    """
    :param player_state: Our state
    :param enemy_state: EnemyState for who we hit

    Usually, the player is responsible for marking themselves as dead when they hit an enemy.

    Set player_state["active"] = False to indicate that we're dying, or enemy_state.active = False to indicate it's dying

    :return: None
    """
    player_state["active"] = False


def collided_with_enemy_missile(player_state, missile_state):
    """
    :param player_state: Our state
    :param missile_state: EnemyMissileState for who we hit

    Usually, the player is responsible for marking themselves as dead when they hit an enemy missile,
    and the missile is responsible for marking itself as stopped when it hits something.

    Set player_state["active"] = False to indicate that we're dying, or missile.active = False to indicate it's dying

    :return: None
    """
    player_state["active"] = False


def collided_with_level(player_state, previous_position):
    """
        Called whenever the player bumps into a wall.
        Usually, you just want to set player_state["position"] = previous_position

    :param player_state: Our state
    :param previous_position: Where were we before be bumped into the wall?
    :return: the new PlayerState
    """
    player_state["position"] = previous_position
    return player_state
