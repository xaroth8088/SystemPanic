class Pak:
    def get_sprite_details(self):
        """
            Tells the game engine how to slice up your spritesheet.

            This should be in the form of a dict, where each key has an array of rect objects, where a rect object
            is defined as a dict with these keys: x, y, width, height

            By the time advance() is called, self.sprites will be set with object of sprite objects in the same shape,
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

    def get_top_left_outer(self):
        """
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called

        Note: self.sprites will be pre-filled with sprite objects before we get here

        :return: which sprite to use.
        """
        return self.sprites["block"][0]

    def get_top_left_inner(self):
        """
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called

        Note: self.sprites will be pre-filled with sprite objects before we get here

        :return: which sprite to use.
        """
        return self.sprites["block"][0]

    def get_top(self):
        """
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called

        Note: self.sprites will be pre-filled with sprite objects before we get here

        :return: which sprite to use.
        """
        return self.sprites["block"][0]

    def get_top_right_outer(self):
        """
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called

        Note: self.sprites will be pre-filled with sprite objects before we get here

        :return: which sprite to use.
        """
        return self.sprites["block"][0]

    def get_top_right_inner(self):
        """
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called

        Note: self.sprites will be pre-filled with sprite objects before we get here

        :return: which sprite to use.
        """
        return self.sprites["block"][0]

    def get_left(self):
        """
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called

        Note: self.sprites will be pre-filled with sprite objects before we get here

        :return: which sprite to use.
        """
        return self.sprites["block"][0]

    def get_center(self):
        """
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called

        Note: self.sprites will be pre-filled with sprite objects before we get here

        :return: which sprite to use.
        """
        return self.sprites["block"][0]

    def get_right(self):
        """
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called

        Note: self.sprites will be pre-filled with sprite objects before we get here

        :return: which sprite to use.
        """
        return self.sprites["block"][0]

    def get_bottom_left_outer(self):
        """
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called

        Note: self.sprites will be pre-filled with sprite objects before we get here

        :return: which sprite to use.
        """
        return self.sprites["block"][0]

    def get_bottom_left_inner(self):
        """
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called

        Note: self.sprites will be pre-filled with sprite objects before we get here

        :return: which sprite to use.
        """
        return self.sprites["block"][0]

    def get_bottom(self):
        """
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called

        Note: self.sprites will be pre-filled with sprite objects before we get here

        :return: which sprite to use.
        """
        return self.sprites["block"][0]

    def get_bottom_right_outer(self):
        """
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called

        Note: self.sprites will be pre-filled with sprite objects before we get here

        :return: which sprite to use.
        """
        return self.sprites["block"][0]

    def get_bottom_right_inner(self):
        """
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called

        Note: self.sprites will be pre-filled with sprite objects before we get here

        :return: which sprite to use.
        """
        return self.sprites["block"][0]
