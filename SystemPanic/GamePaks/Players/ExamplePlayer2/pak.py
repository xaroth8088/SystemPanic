import random

import pygame


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
        "Basic sedan car": [
            {
                "image rect": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
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
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 0,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 96,
                    "y": 0,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
            {
                "image rect": {
                    "x": 128,
                    "y": 0,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 160,
                    "y": 0,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 192,
                    "y": 0,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 224,
                    "y": 0,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
        ],
        "Sport coupe": [
            {
                "image rect": {
                    "x": 0,
                    "y": 32,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 32,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 32,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 96,
                    "y": 32,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
            {
                "image rect": {
                    "x": 128,
                    "y": 32,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 160,
                    "y": 32,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 192,
                    "y": 32,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 224,
                    "y": 32,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
        ],
        "Hothatch car": [
            {
                "image rect": {
                    "x": 0,
                    "y": 64,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 64,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 64,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 96,
                    "y": 64,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
            {
                "image rect": {
                    "x": 128,
                    "y": 64,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 160,
                    "y": 64,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 192,
                    "y": 64,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 224,
                    "y": 64,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
        ],
        "Small delivery car": [
            {
                "image rect": {
                    "x": 0,
                    "y": 96,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 96,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 96,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 96,
                    "y": 96,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
            {
                "image rect": {
                    "x": 128,
                    "y": 96,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 160,
                    "y": 96,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 192,
                    "y": 96,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 224,
                    "y": 96,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
        ],
        "Station wagon": [
            {
                "image rect": {
                    "x": 0,
                    "y": 128,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 128,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 128,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 96,
                    "y": 128,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
            {
                "image rect": {
                    "x": 128,
                    "y": 128,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 160,
                    "y": 128,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 192,
                    "y": 128,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 224,
                    "y": 128,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
        ],
        "Minibus": [
            {
                "image rect": {
                    "x": 0,
                    "y": 160,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 160,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 160,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 96,
                    "y": 160,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
            {
                "image rect": {
                    "x": 128,
                    "y": 160,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 160,
                    "y": 160,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 192,
                    "y": 160,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 224,
                    "y": 160,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
        ],
        "Delivery van": [
            {
                "image rect": {
                    "x": 0,
                    "y": 192,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 192,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 192,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 96,
                    "y": 192,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
            {
                "image rect": {
                    "x": 128,
                    "y": 192,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 160,
                    "y": 192,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 192,
                    "y": 192,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 224,
                    "y": 192,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
        ],
        "Pickup truck": [
            {
                "image rect": {
                    "x": 0,
                    "y": 224,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 32,
                    "y": 224,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 64,
                    "y": 224,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 96,
                    "y": 224,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
            },
            {
                "image rect": {
                    "x": 128,
                    "y": 224,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 160,
                    "y": 224,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 4,
                    "y": 8,
                    "width": 24,
                    "height": 15
                },
            },
            {
                "image rect": {
                    "x": 192,
                    "y": 224,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            },
            {
                "image rect": {
                    "x": 224,
                    "y": 224,
                    "width": 32,
                    "height": 32

                },
                "hitbox": {
                    "x": 10,
                    "y": 7,
                    "width": 12,
                    "height": 18
                },
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
    player_state = game_state[key][index]

    driving_speed = 70.0
    car_type = player_state["pak_specific_state"].get("type")

    # State specific to us
    if car_type is None:
        car_type = random.choice(list(sprites.keys()))
        player_state["pak_specific_state"]["type"] = car_type

        # We can also see this as an initialization state
        player_state["facing"] = {
            "x": -1,
            "y": 0
        }
        player_state["sprite"] = sprites[car_type][1]
        player_state["pak_specific_state"]["angle"] = 0

    # What size should our sprite be drawn on-screen as?
    player_state["sprite_size"]["width"] = 16
    player_state["sprite_size"]["height"] = 16

    # How are we moving?  And what's our sprite?
    turning_speed = 360.0  # Degrees per second

    # TODO: change this to rotate left/right, and have sprite selected by approximate angle
    # TODO: change up/down to be accel/deccel
    if game_state["pressed_buttons"]["left"] is True:
        player_state["pak_specific_state"]["angle"] -= turning_speed * delta_t

    if game_state["pressed_buttons"]["right"] is True:
        player_state["pak_specific_state"]["angle"] += turning_speed * delta_t

    # Normalize the angle
    player_state["pak_specific_state"]["angle"] %= 360.0
    while player_state["pak_specific_state"]["angle"] < 0:
        player_state["pak_specific_state"]["angle"] += 360.0

    if 22.5 < player_state["pak_specific_state"]["angle"] <= 67.5:
        player_state["sprite"] = sprites[car_type][4]
    elif 67.5 < player_state["pak_specific_state"]["angle"] <= 112.5:
        player_state["sprite"] = sprites[car_type][5]
    elif 112.5 < player_state["pak_specific_state"]["angle"] <= 157.5:
        player_state["sprite"] = sprites[car_type][6]
    elif 157.5 < player_state["pak_specific_state"]["angle"] <= 202.5:
        player_state["sprite"] = sprites[car_type][7]
    elif 202.5 < player_state["pak_specific_state"]["angle"] <= 247.5:
        player_state["sprite"] = sprites[car_type][0]
    elif 247.5 < player_state["pak_specific_state"]["angle"] <= 292.5:
        player_state["sprite"] = sprites[car_type][1]
    elif 292.5 < player_state["pak_specific_state"]["angle"] <= 337.5:
        player_state["sprite"] = sprites[car_type][2]
    else:
        player_state["sprite"] = sprites[car_type][3]

    vector = pygame.math.Vector2(0, -1)
    vector.rotate_ip(player_state["pak_specific_state"]["angle"])

    player_state["position"]["x"] += driving_speed * delta_t * vector.x
    player_state["position"]["y"] += driving_speed * delta_t * vector.y

    if game_state["pressed_buttons"]["fire"] is True:
        # Limit firing to once per 0.5 seconds
        last_fired = player_state["pak_specific_state"].get("last_fired")

        if last_fired is None or time_since_start - last_fired > 0.5:
            new_missiles.append(
                {
                    "target": "enemy",
                    "direction": {
                        "x": vector.x,
                        "y": vector.y
                    },
                    "position": {
                        "x": player_state["position"]["x"] + vector.x * 16,
                        "y": player_state["position"]["y"] + vector.y * 16
                    }
                }
            )
            player_state["pak_specific_state"]["last_fired"] = time_since_start

    # How do we interact with the borders of the screen?
    # TODO: make the game engine actually handle this using these variables, instead of doing it here
    player_state["wrap_x"] = True
    player_state["wrap_y"] = True

    if player_state["position"]["x"] < 0:
        player_state["position"]["x"] = 0
    if player_state["position"]["x"] > 320:
        player_state["position"]["x"] = 320
    if player_state["position"]["y"] < 0:
        player_state["position"]["y"] = 0
    if player_state["position"]["y"] > 240:
        player_state["position"]["y"] = 240

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
