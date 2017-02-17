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
        return {
            "missile": [
                {
                    "x": 0,
                    "y": 0,
                    "width": 8,
                    "height": 8
                },
            ]
        }

    def advance(self, missile_state, all_states, time_since_start, delta_t, target):
        """
        :param missile_state: the MissileState
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called
        :param target: One of "player" or "enemy".  E.g. A missile fired by a player will have a target of "enemy".

        :return: the new MissileState
        """
        # What size should our sprite be drawn on-screen as?
        missile_state["sprite_size"]["width"] = 16
        missile_state["sprite_size"]["height"] = 16

        # What's our hitbox rect (relative to the top-left corner of the sprite)?
        missile_state["hitbox"]["x"] = 0
        missile_state["hitbox"]["y"] = 0
        missile_state["hitbox"]["width"] = 32
        missile_state["hitbox"]["height"] = 32

        # How are we moving?  And what's our sprite?
        missile_state["position"]["x"] += 128 * delta_t * missile_state["direction"]["x"]
        missile_state["position"]["y"] += 128 * delta_t * missile_state["direction"]["y"]
        missile_state["sprite"] = self.sprites["missile"][0]   # No animation for this one

        # Should we die?
        if time_since_start - missile_state["start_time"] > 0.5:
            missile_state["active"] = False

        # How do we interact with the borders of the screen?
        # TODO: make the game engine actually handle this using these variables, instead of doing it here
        missile_state["wrap_x"] = True
        missile_state["wrap_y"] = True

        if missile_state["position"]["x"] < 0:
            missile_state["position"]["x"] = 0
        if missile_state["position"]["x"] > 800:
            missile_state["position"]["x"] = 800
        if missile_state["position"]["y"] < 0:
            missile_state["position"]["y"] = 0
        if missile_state["position"]["y"] > 600:
            missile_state["position"]["y"] = 600

        # Return the new state
        return missile_state

    def collided_with_player(self, missile_state, player_state):
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

    def collided_with_enemy(self, missile_state, enemy_state):
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

    def collided_with_level(self, missile_state, previous_position):
        """
            Called whenever the player bumps into a wall.
            Usually, you just want to set missile_state["active"] = False

        :param missile_state: Our state
        :param previous_position: Where were we before be bumped into the wall?
        :return: the new MissileState
        """
        missile_state["active"] = False
        return missile_state
