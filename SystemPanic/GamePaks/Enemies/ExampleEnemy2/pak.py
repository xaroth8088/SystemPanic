import random


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
        "green": [
            {
                "image rect": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 0,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 0,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 0,
                    "y": 32,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 32,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 32,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 0,
                    "y": 64,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 64,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 64,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 0,
                    "y": 96,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 96,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 96,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
        ],
        "red": [
            {
                "image rect": {
                    "x": 0,
                    "y": 128,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 128,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 128,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 0,
                    "y": 160,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 160,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 160,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 0,
                    "y": 192,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 192,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 192,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 0,
                    "y": 224,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 224,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 224,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
        ],
        "blue": [
            {
                "image rect": {
                    "x": 0,
                    "y": 256,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 256,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 256,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 0,
                    "y": 288,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 288,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 288,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 0,
                    "y": 320,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 320,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 320,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 0,
                    "y": 352,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 352,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 352,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
        ],
        "gray": [
            {
                "image rect": {
                    "x": 0,
                    "y": 384,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 384,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 384,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 0,
                    "y": 416,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 416,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 416,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 0,
                    "y": 448,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 448,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 448,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 0,
                    "y": 480,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 480,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 480,
                    "width": 32,
                    "height": 32,
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                }
            },
        ],
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
    enemy_state = game_state[key][index]

    # State specific to us
    color = enemy_state["pak_specific_state"].get("color")

    if color is None:
        color = random.choice(list(sprites.keys()))
        enemy_state["pak_specific_state"]["color"] = color
        enemy_state["sprite"] = sprites[color][random.randint(0, 8)]

    size = enemy_state["pak_specific_state"].get("size")

    if size is None:
        size = random.randint(8, 32)
        enemy_state["pak_specific_state"]["size"] = size
        enemy_state["sprite_size"]["width"] = size
        enemy_state["sprite_size"]["height"] = size

    # How are we moving?  And what's our sprite?
    # Flee player, dumb
    player_x = game_state["players"][0]["position"]["x"]
    player_y = game_state["players"][0]["position"]["y"]

    speed = 16.0
    if enemy_state["position"]["x"] < player_x:
        enemy_state["position"]["x"] -= speed * delta_t
    else:
        enemy_state["position"]["x"] += speed * delta_t

    if enemy_state["position"]["y"] < player_y:
        enemy_state["position"]["y"] -= speed * delta_t
    else:
        enemy_state["position"]["y"] += speed * delta_t

    if random.randint(0, 100) == 0:
        enemy_state["sprite"] = sprites[color][random.randint(0, 8)]

    # Do we want to fire a missile?
    # Fire every 1.5 seconds, aimed at the player
    last_fired = enemy_state["pak_specific_state"].get("last_fired")

    if last_fired is None or time_since_start - last_fired > 1.5:
        new_missiles.append({
            "target": "player",
            "direction": {
                "x": player_x - enemy_state["position"]["x"],
                "y": player_y - enemy_state["position"]["y"]
            },
            "position": enemy_state["position"].copy()
        })
        enemy_state["pak_specific_state"]["last_fired"] = time_since_start

    # How do we interact with the borders of the screen?
    enemy_state["wrap_x"] = False
    enemy_state["wrap_y"] = False

    # Return the new state
    return game_state


def collided_with_player(enemy_state, player_state):
    """
    :param enemy_state: Our state
    :param player_state: PlayerState for who we hit

    Usually, the player is responsible for marking themselves as dead when they hit an enemy.

    Set enemy_state["active"] = False to indicate that we're dying, or player_state["active"] = False to indicate it's dying

    :return: None
    """
    pass


def collided_with_player_missile(enemy_state, missile_state):
    """
    :param enemy_state: Our state
    :param missile_state: PlayerState for who we hit

    Usually, the enemy is responsible for marking themselves as dead when they hit a player missile,
    and the missile is responsible for marking itself as stopped when it hits something.

    Set enemy_state["active"] = False to indicate that we're dying, or missile["active"] = False to indicate it's dying

    :return: None
    """
    enemy_state["active"] = False


def collided_with_level(enemy_state, previous_position):
    """
        Called whenever the player bumps into a wall.
        Usually, you just want to set enemy_state["position"] = previous_position

    :param enemy_state: Our state
    :param previous_position: Where were we before be bumped into the wall?
    :return: the new EnemyState
    """
    enemy_state["position"] = previous_position
    return enemy_state
