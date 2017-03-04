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
        "spinner": [
            {
                "image rect": {
                    "x": 0,
                    "y": 0,
                    "width": 16,
                    "height": 16
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 16,
                    "height": 16
                }
            },
            {
                "image rect": {
                    "x": 16,
                    "y": 0,
                    "width": 16,
                    "height": 16
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 16,
                    "height": 16
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 0,
                    "width": 16,
                    "height": 16
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 16,
                    "height": 16
                }
            },
            {
                "image rect": {
                    "x": 48,
                    "y": 0,
                    "width": 16,
                    "height": 16
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 16,
                    "height": 16
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 0,
                    "width": 16,
                    "height": 16
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 16,
                    "height": 16
                }
            },
            {
                "image rect": {
                    "x": 80,
                    "y": 0,
                    "width": 16,
                    "height": 16
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 16,
                    "height": 16
                }
            },
            {
                "image rect": {
                    "x": 96,
                    "y": 0,
                    "width": 16,
                    "height": 16
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 16,
                    "height": 16
                }
            },
            {
                "image rect": {
                    "x": 112,
                    "y": 0,
                    "width": 16,
                    "height": 16
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 16,
                    "height": 16
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
    missile_state = game_state[key][index]

    lifetime = 0.75  # in seconds

    # What size should our sprite be drawn on-screen as?
    time_alive_ratio = (time_since_start - missile_state["start_time"]) / lifetime
    size = 24 * (1 - time_alive_ratio)
    missile_state["sprite_size"]["width"] = int(size)
    missile_state["sprite_size"]["height"] = int(size)

    # How are we moving?  And what's our sprite?
    missile_state["position"]["x"] += 96 * delta_t * missile_state["direction"]["x"]
    missile_state["position"]["y"] += 96 * delta_t * missile_state["direction"]["y"]

    missile_state["sprite"] = sprites["spinner"][int(time_since_start * 16) % 8]

    # Should we die?
    if time_since_start - missile_state["start_time"] > lifetime:
        missile_state["active"] = False

    # How do we interact with the borders of the screen?
    # TODO: make the game engine actually handle this using these variables, instead of doing it here
    missile_state["wrap_x"] = True
    missile_state["wrap_y"] = True

    if missile_state["position"]["x"] < 0:
        missile_state["position"]["x"] = 0
    if missile_state["position"]["x"] > 320:
        missile_state["position"]["x"] = 320
    if missile_state["position"]["y"] < 0:
        missile_state["position"]["y"] = 0
    if missile_state["position"]["y"] > 240:
        missile_state["position"]["y"] = 240

    # Return the new state
    return game_state


def collided_with_player(missile_state, player_state):
    """
    :param missile_state: Our state
    :param player_state: PlayerState for who we hit

    This will only be called when our target was "player" (i.e. if we were fired by an enemy)

    Usually, the player is responsible for marking themselves as dead when they hit an enemy missile,
    and the missile is responsible for marking itself as stopped when it hits something.

    Set missile_state["active"] = False to indicate that we're dying, or player_state["active"] = False to indicate it's dying

    :return: None
    """
    missile_state["active"] = False


def collided_with_enemy(missile_state, enemy_state):
    """
    :param missile_state: Our state
    :param enemy_state: EnemyState for who we hit

    This will only be called when our target was "enemy" (i.e. if we were fired by a player)

    Usually, the enemy is responsible for marking themselves as dead when they hit an player missile,
    and the missile is responsible for marking itself as stopped when it hits something.

    Set missile_state["active"] = False to indicate that we're dying, or enemy_state["active"] = False to indicate it's dying

    :return: None
    """
    missile_state["active"] = False


def collided_with_level(missile_state, previous_position):
    """
        Called whenever the player bumps into a wall.
        Usually, you just want to set missile_state["active"] = False

    :param missile_state: Our state
    :param previous_position: Where were we before be bumped into the wall?
    :return: the new MissileState
    """
    missile_state["active"] = False
    return missile_state
