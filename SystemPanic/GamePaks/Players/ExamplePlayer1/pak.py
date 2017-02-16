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
            "left": [
                {
                    "x": 0,
                    "y": 512,
                    "width": 256,
                    "height": 256
                },
                {
                    "x": 256,
                    "y": 512,
                    "width": 256,
                    "height": 256
                },
                {
                    "x": 512,
                    "y": 512,
                    "width": 256,
                    "height": 256
                },
                {
                    "x": 768,
                    "y": 512,
                    "width": 256,
                    "height": 256
                },
            ],
            "right": [
                {
                    "x": 0,
                    "y": 768,
                    "width": 256,
                    "height": 256
                },
                {
                    "x": 256,
                    "y": 768,
                    "width": 256,
                    "height": 256
                },
                {
                    "x": 512,
                    "y": 768,
                    "width": 256,
                    "height": 256
                },
                {
                    "x": 768,
                    "y": 768,
                    "width": 256,
                    "height": 256
                },
            ],
            "up": [
                {
                    "x": 0,
                    "y": 256,
                    "width": 256,
                    "height": 256
                },
                {
                    "x": 256,
                    "y": 256,
                    "width": 256,
                    "height": 256
                },
                {
                    "x": 512,
                    "y": 256,
                    "width": 256,
                    "height": 256
                },
                {
                    "x": 768,
                    "y": 256,
                    "width": 256,
                    "height": 256
                },
            ],
            "down": [
                {
                    "x": 0,
                    "y": 0,
                    "width": 256,
                    "height": 256
                },
                {
                    "x": 256,
                    "y": 0,
                    "width": 256,
                    "height": 256
                },
                {
                    "x": 512,
                    "y": 0,
                    "width": 256,
                    "height": 256
                },
                {
                    "x": 768,
                    "y": 0,
                    "width": 256,
                    "height": 256
                },
            ]
        }

    def advance(self, player_state, all_states, time_since_start, delta_t, pressed_buttons, new_missiles):
        """
        :param player_state: the PlayerState
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called
        :param pressed_buttons: A dict of the controls that are currently active.  Includes:
            "up", "down", "left", "right", "fire"
        :param new_missiles: If you want to fire a new missile, append a dict for each new missile with
            a dict like: {
                "direction": { "x": #, "y": # },
                "position": { "x": #, "y": # }
            }
            The vector need not be normalized. Note that the missile may choose to override this direction once fired!

        :return: the new PlayerState
        """
        # What size should our sprite be drawn on-screen as?
        player_state.sprite_size["width"] = 32
        player_state.sprite_size["height"] = 32

        # What's our hitbox rect (relative to the top-left corner of the sprite)?
        player_state.hitbox = {
            "x":0,
            "y": 0,
            "width": 32,
            "height": 32
        }

        # How are we moving?  And what's our sprite?
        player_state.sprite = self.sprites["down"][0]  # "Idle"

        walking_speed = 128.0

        if pressed_buttons["left"] is True:
            player_state.position["x"] -= walking_speed * delta_t
            player_state.sprite = self.sprites["left"][int(time_since_start * 8) % 4]
        if pressed_buttons["right"] is True:
            player_state.position["x"] += walking_speed * delta_t
            player_state.sprite = self.sprites["right"][int(time_since_start * 8) % 4]
        if pressed_buttons["up"] is True:
            player_state.position["y"] -= walking_speed * delta_t
            player_state.sprite = self.sprites["up"][int(time_since_start * 8) % 4]
        if pressed_buttons["down"] is True:
            player_state.position["y"] += walking_speed * delta_t
            player_state.sprite = self.sprites["down"][int(time_since_start * 8) % 4]

        if pressed_buttons["fire"] is True:
            # Limit firing to once per 0.5 seconds
            last_fired = player_state.get_pak_specific_state("last_fired")
            if last_fired is None or time_since_start - last_fired > 0.5:
                new_missiles.append(
                    {
                        "direction": {"x": 1.0, "y": 0.0},
                        "position": {"x": player_state.position["x"], "y": player_state.position["y"]}
                    }
                )
                player_state.set_pak_specific_state("last_fired", time_since_start)

        # How do we interact with the borders of the screen?
        # TODO: make the game engine actually handle this using these variables, instead of doing it here
        player_state.wrap_x = True
        player_state.wrap_y = True

        if player_state.position["x"] < 0:
            player_state.position["x"] = 0
        if player_state.position["x"] > 800:
            player_state.position["x"] = 800
        if player_state.position["y"] < 0:
            player_state.position["y"] = 0
        if player_state.position["y"] > 600:
            player_state.position["y"] = 600

        # Return the new state
        return player_state

    def collided_with_enemy(self, player_state, enemy_state):
        """
        :param player_state: Our state
        :param enemy_state: EnemyState for who we hit

        Usually, the player is responsible for marking themselves as dead when they hit an enemy.

        Set player_state.active = False to indicate that we're dying, or enemy_state.active = False to indicate it's dying

        :return: None
        """
        player_state.active = False

    def collided_with_enemy_missile(self, player_state, missile_state):
        """
        :param player_state: Our state
        :param missile_state: EnemyMissileState for who we hit

        Usually, the player is responsible for marking themselves as dead when they hit an enemy missile,
        and the missile is responsible for marking itself as stopped when it hits something.

        Set player_state.active = False to indicate that we're dying, or missile.active = False to indicate it's dying

        :return: None
        """
        player_state.active = False

    def collided_with_level(self, player_state, previous_position):
        """
            Called whenever the player bumps into a wall.
            Usually, you just want to set player_state.position = previous_position

        :param player_state: Our state
        :param previous_position: Where were we before be bumped into the wall?
        :return: the new PlayerState
        """
        player_state.position = previous_position
        return player_state
