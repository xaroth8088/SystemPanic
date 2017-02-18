import random


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
            "Basic sedan car": [
                {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 32,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 64,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 96,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 128,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 160,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 192,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 224,
                    "y": 0,
                    "width": 32,
                    "height": 32
                },
            ],
            "Sport coupe": [
                {
                    "x": 0,
                    "y": 32,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 32,
                    "y": 32,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 64,
                    "y": 32,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 96,
                    "y": 32,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 128,
                    "y": 32,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 160,
                    "y": 32,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 192,
                    "y": 32,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 224,
                    "y": 32,
                    "width": 32,
                    "height": 32
                },
            ],
            "Hothatch car": [
                {
                    "x": 0,
                    "y": 64,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 32,
                    "y": 64,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 64,
                    "y": 64,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 96,
                    "y": 64,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 128,
                    "y": 64,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 160,
                    "y": 64,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 192,
                    "y": 64,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 224,
                    "y": 64,
                    "width": 32,
                    "height": 32
                },
            ],
            "Small delivery car": [
                {
                    "x": 0,
                    "y": 96,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 32,
                    "y": 96,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 64,
                    "y": 96,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 96,
                    "y": 96,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 128,
                    "y": 96,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 160,
                    "y": 96,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 192,
                    "y": 96,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 224,
                    "y": 96,
                    "width": 32,
                    "height": 32
                },
            ],
            "Station wagon": [
                {
                    "x": 0,
                    "y": 128,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 32,
                    "y": 128,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 64,
                    "y": 128,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 96,
                    "y": 128,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 128,
                    "y": 128,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 160,
                    "y": 128,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 192,
                    "y": 128,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 224,
                    "y": 128,
                    "width": 32,
                    "height": 32
                },
            ],
            "Minibus": [
                {
                    "x": 0,
                    "y": 160,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 32,
                    "y": 160,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 64,
                    "y": 160,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 96,
                    "y": 160,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 128,
                    "y": 160,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 160,
                    "y": 160,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 192,
                    "y": 160,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 224,
                    "y": 160,
                    "width": 32,
                    "height": 32
                },
            ],
            "Delivery van": [
                {
                    "x": 0,
                    "y": 192,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 32,
                    "y": 192,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 64,
                    "y": 192,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 96,
                    "y": 192,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 128,
                    "y": 192,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 160,
                    "y": 192,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 192,
                    "y": 192,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 224,
                    "y": 192,
                    "width": 32,
                    "height": 32
                },
            ],
            "Pickup truck": [
                {
                    "x": 0,
                    "y": 224,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 32,
                    "y": 224,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 64,
                    "y": 224,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 96,
                    "y": 224,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 128,
                    "y": 224,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 160,
                    "y": 224,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 192,
                    "y": 224,
                    "width": 32,
                    "height": 32
                },
                {
                    "x": 224,
                    "y": 224,
                    "width": 32,
                    "height": 32
                },
            ],
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
        driving_speed = 256.0
        car_type = player_state["pak_specific_state"].get("type")

        # State specific to us
        if car_type is None:
            car_type = random.choice(list(self.get_sprite_details().keys()))
            player_state["pak_specific_state"]["type"] = car_type

            # We can also see this as an initialization state
            player_state["facing"] = {
                "x": -1,
                "y": 0
            }
            player_state["sprite"] = self.sprites[car_type][1]

        # What size should our sprite be drawn on-screen as?
        player_state["sprite_size"]["width"] = 32
        player_state["sprite_size"]["height"] = 32

        # How are we moving?  And what's our sprite?
        # And what's our hitbox rect (relative to the top-left corner of the sprite)?
        # TODO: change this to rotate left/right, and have sprite selected by approximate angle
        # TODO: change up/down to be accel/deccel
        if pressed_buttons["left"] is True:
            player_state["facing"] = {
                "x": -1,
                "y": 0
            }
            player_state["hitbox"] = {
                "x": 4,
                "y": 8,
                "width": 24,
                "height": 15
            }
            player_state["sprite"] = self.sprites[car_type][1]
        if pressed_buttons["right"] is True:
            player_state["facing"] = {
                "x": 1,
                "y": 0
            }
            player_state["hitbox"] = {
                "x": 4,
                "y": 8,
                "width": 24,
                "height": 15
            }
            player_state["sprite"] = self.sprites[car_type][5]
        if pressed_buttons["up"] is True:
            player_state["facing"] = {
                "x": 0,
                "y": -1
            }
            player_state["hitbox"] = {
                "x": 10,
                "y": 7,
                "width": 12,
                "height": 18
            }
            player_state["sprite"] = self.sprites[car_type][3]
        if pressed_buttons["down"] is True:
            player_state["facing"] = {
                "x": 0,
                "y": 1
            }
            player_state["hitbox"] = {
                "x": 10,
                "y": 7,
                "width": 12,
                "height": 18
            }
            player_state["sprite"] = self.sprites[car_type][7]

        player_state["position"]["x"] += driving_speed * delta_t * player_state["facing"]["x"]
        player_state["position"]["y"] += driving_speed * delta_t * player_state["facing"]["y"]

        if pressed_buttons["fire"] is True:
            # Limit firing to once per 0.5 seconds
            last_fired = player_state["pak_specific_state"].get("last_fired")

            if last_fired is None or time_since_start - last_fired > 0.5:
                new_missiles.append(
                    {
                        "direction": player_state["facing"],
                        "position": {
                            "x": player_state["position"]["x"] + player_state["facing"]["x"] * 16,
                            "y": player_state["position"]["y"] + player_state["facing"]["y"] * 16
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
        if player_state["position"]["x"] > 800:
            player_state["position"]["x"] = 800
        if player_state["position"]["y"] < 0:
            player_state["position"]["y"] = 0
        if player_state["position"]["y"] > 600:
            player_state["position"]["y"] = 600

        # Return the new state
        return player_state

    def collided_with_enemy(self, player_state, enemy_state):
        """
        :param player_state: Our state
        :param enemy_state: EnemyState for who we hit

        Usually, the player is responsible for marking themselves as dead when they hit an enemy.

        Set player_state["active"] = False to indicate that we're dying, or enemy_state.active = False to indicate it's dying

        :return: None
        """
        player_state["active"] = False

    def collided_with_enemy_missile(self, player_state, missile_state):
        """
        :param player_state: Our state
        :param missile_state: EnemyMissileState for who we hit

        Usually, the player is responsible for marking themselves as dead when they hit an enemy missile,
        and the missile is responsible for marking itself as stopped when it hits something.

        Set player_state["active"] = False to indicate that we're dying, or missile.active = False to indicate it's dying

        :return: None
        """
        player_state["active"] = False

    def collided_with_level(self, player_state, previous_position):
        """
            Called whenever the player bumps into a wall.
            Usually, you just want to set player_state["position"] = previous_position

        :param player_state: Our state
        :param previous_position: Where were we before be bumped into the wall?
        :return: the new PlayerState
        """
        player_state["position"] = previous_position
        return player_state
