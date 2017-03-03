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
    # TODO: do we need to do something about the collision sizes here, too?  Probably.
    # TODO: when we do that, we'll need to keep in mind that the actual size of the block gets scaled later.
    return {
        "block": [
            {
                "image rect": {
                    "x": 0,
                    "y": 0,
                    "width": 128,
                    "height": 128
                },
                "hitbox": {
                    "x": 0,
                    "y": 0,
                    "width": 128,
                    "height": 128
                }
            }
        ],
    }


def get_top_left_outer(sprites):
    """
    :return: which sprite to use.
    """
    return sprites["block"][0]


def get_top_left_inner(sprites):
    """
    :return: which sprite to use.
    """
    return sprites["block"][0]


def get_top(sprites):
    """
    :return: which sprite to use.
    """
    return sprites["block"][0]


def get_top_right_outer(sprites):
    """
    :return: which sprite to use.
    """
    return sprites["block"][0]


def get_top_right_inner(sprites):
    """
    :return: which sprite to use.
    """
    return sprites["block"][0]


def get_left(sprites):
    """
    :return: which sprite to use.
    """
    return sprites["block"][0]


def get_center(sprites):
    """
    :return: which sprite to use.
    """
    return sprites["block"][0]


def get_right(sprites):
    """
    :return: which sprite to use.
    """
    return sprites["block"][0]


def get_bottom_left_outer(sprites):
    """
    :return: which sprite to use.
    """
    return sprites["block"][0]


def get_bottom_left_inner(sprites):
    """
    :return: which sprite to use.
    """
    return sprites["block"][0]


def get_bottom(sprites):
    """
    :return: which sprite to use.
    """
    return sprites["block"][0]


def get_bottom_right_outer(sprites):
    """
    :return: which sprite to use.
    """
    return sprites["block"][0]


def get_bottom_right_inner(sprites):
    """
    :return: which sprite to use.
    """
    return sprites["block"][0]
