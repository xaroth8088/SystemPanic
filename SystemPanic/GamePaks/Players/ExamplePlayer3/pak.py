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
    sprites = {}

    sprites["idle right"] = []
    for x in range(0, 4):
        sprites["idle right"].append({
            "image rect": {
                "x": 18 * x,
                "y": 0,
                "width": 18,
                "height": 18
            },
            "hitbox": {
                "x": 0,
                "y": 0,
                "width": 18,
                "height": 18
            }
        })

    sprites["idle left"] = []
    for x in range(2, 6):
        sprites["idle left"].append({
            "image rect": {
                "x": 18 * x,
                "y": 36,
                "width": 18,
                "height": 18
            },
            "hitbox": {
                "x": 0,
                "y": 0,
                "width": 18,
                "height": 18
            }
        })

    sprites["right"] = []
    for x in range(0, 6):
        sprites["right"].append({
            "image rect": {
                "x": 18 * x,
                "y": 18,
                "width": 18,
                "height": 18
            },
            "hitbox": {
                "x": 0,
                "y": 0,
                "width": 18,
                "height": 18
            }
        })

    sprites["left"] = []
    for x in range(0, 6):
        sprites["left"].append({
            "image rect": {
                "x": 18 * x,
                "y": 54,
                "width": 18,
                "height": 18
            },
            "hitbox": {
                "x": 0,
                "y": 0,
                "width": 18,
                "height": 18
            }
        })

    return sprites


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

    walking_speed = 64.0
    gravity = 128.0
    jump_speed = 128.0

    # State specific to us, if any

    # What size should our sprite be drawn on-screen as?
    player_state["sprite_size"]["width"] = 18
    player_state["sprite_size"]["height"] = 18

    # How are we moving?  And what's our sprite?

    idle = True

    # We're never facing anywhere other than left or right
    player_state["facing"]["y"] = 0

    # Are we on the ground?
    # TODO: make this something the game engine does for us, as part of the physics engine
    on_ground = False
    for wall in game_state["walls"]:
        wall_rect = pygame.Rect(
            wall["position"]["x"] - wall["sprite_size"]["width"] / 2,
            wall["position"]["y"] - wall["sprite_size"]["height"] / 2,
            wall["sprite_size"]["width"],
            wall["sprite_size"]["height"]
        )
        if wall_rect.collidepoint(
            player_state["position"]["x"] - player_state["sprite_size"]["width"] / 2.0,
            player_state["position"]["y"] + player_state["sprite_size"]["height"] / 2.0
        ) or wall_rect.collidepoint(
            player_state["position"]["x"] + player_state["sprite_size"]["width"] / 2.0,
            player_state["position"]["y"] + player_state["sprite_size"]["height"] / 2.0
        ):
            on_ground = True
            break
    if player_state["position"]["y"] >= 240:
        on_ground = True

    # Apply gravity
    if on_ground is False:
        player_state["velocity"]["y"] += gravity * delta_t

    # No momentum in the air - only if the player is moving
    if game_state["pressed_buttons"]["left"] is False and game_state["pressed_buttons"]["right"] is False:
        player_state["velocity"]["x"] = 0

    if game_state["pressed_buttons"]["left"] is True:
        player_state["facing"]["x"] = -1
        player_state["velocity"]["x"] = -walking_speed
        idle = False

    if game_state["pressed_buttons"]["right"] is True:
        player_state["facing"]["x"] = 1
        player_state["velocity"]["x"] = walking_speed
        idle = False

    if game_state["pressed_buttons"]["up"] is True and on_ground is True:
        player_state["velocity"]["y"] = -1.0 * jump_speed

    if game_state["pressed_buttons"]["fire"] is True:
        # Limit firing to once per 0.7 seconds
        last_fired = player_state["pak_specific_state"].get("last_fired")

        if last_fired is None or time_since_start - last_fired > 0.7:
            new_missiles.append(
                {
                    "target": "enemy",
                    "direction": player_state["facing"],
                    "position": {
                        "x": player_state["position"]["x"] + player_state["facing"]["x"] * 16,
                        "y": player_state["position"]["y"] + player_state["facing"]["y"] * 16
                    }
                }
            )
            player_state["pak_specific_state"]["last_fired"] = time_since_start

    # Actually move us
    player_state["position"]["x"] += player_state["velocity"]["x"] * delta_t
    player_state["position"]["y"] += player_state["velocity"]["y"] * delta_t

    # Pick our sprite
    if player_state["facing"]["x"] >= 0:
        if idle is True:
            player_state["sprite"] = sprites["idle right"][int(time_since_start * 8) % 4]
        else:
            player_state["sprite"] = sprites["right"][int(time_since_start * 8) % 6]
    else:
        if idle is True:
            player_state["sprite"] = sprites["idle left"][int(time_since_start * 8) % 4]
        else:
            player_state["sprite"] = sprites["left"][int(time_since_start * 8) % 6]

    # How do we interact with the borders of the screen?
    player_state["wrap_x"] = True
    player_state["wrap_y"] = False

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
    # Stop moving vertically whenever we bump into a wall
    player_state["velocity"]["y"] = 0
    player_state["position"] = previous_position
    return player_state
