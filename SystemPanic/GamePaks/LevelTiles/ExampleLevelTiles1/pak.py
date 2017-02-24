def get_sprite_details():
    """
        Tells the game engine how to slice up your spritesheet.

        This should be in the form of a dict, where each key has an array of rect objects, where a rect object
        is defined as a dict with these keys: x, y, width, height

        Later, when a block accessor method is called, it will receive an object of sprite objects in the same shape,
        except the rect objects will be replaced with the sprite objects that you can set on the player state.
    :return:
    """
    # TODO: do we need to do something about the collision sizes here, too?  Probably.
    # TODO: when we do that, we'll need to keep in mind that the actual size of the block gets scaled later.
    return {
        "block": [
            {
                "x": 0,
                "y": 0,
                "width": 128,
                "height": 128
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
