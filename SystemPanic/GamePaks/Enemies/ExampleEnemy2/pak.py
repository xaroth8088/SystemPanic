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
            "green": [
                {
                    "x": 0,
                    "y": 0,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 0,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 0,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 0,
                    "y": 32,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 32,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 32,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 0,
                    "y": 64,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 64,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 64,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 0,
                    "y": 96,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 96,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 96,
                    "width": 32,
                    "height": 32,
                },
            ],
            "red": [
                {
                    "x": 0,
                    "y": 128,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 128,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 128,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 0,
                    "y": 160,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 160,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 160,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 0,
                    "y": 192,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 192,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 192,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 0,
                    "y": 224,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 224,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 224,
                    "width": 32,
                    "height": 32,
                },
            ],
            "blue": [
                {
                    "x": 0,
                    "y": 256,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 256,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 256,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 0,
                    "y": 288,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 288,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 288,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 0,
                    "y": 320,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 320,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 320,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 0,
                    "y": 352,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 352,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 352,
                    "width": 32,
                    "height": 32,
                },
            ],
            "gray": [
                {
                    "x": 0,
                    "y": 384,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 384,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 384,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 0,
                    "y": 416,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 416,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 416,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 0,
                    "y": 448,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 448,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 448,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 0,
                    "y": 480,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 32,
                    "y": 480,
                    "width": 32,
                    "height": 32,
                },
                {
                    "x": 64,
                    "y": 480,
                    "width": 32,
                    "height": 32,
                },
            ],
        }

    def advance(self, enemy_state, all_states, time_since_start, delta_t, new_missiles):
        """
        :param enemy_state: the EnemyState
        :param all_states: a dict with all the game state you might want to examine.  Includes:
            "player", "enemies", "player_missiles", "enemy_missiles", "level"
        :param time_since_start: time in seconds from game start (useful for animation)
        :param delta_t: time in seconds since we were last called
        :param new_missiles: If you want to fire a new missile, append a dict for each new missile with
            a dict like: {
                "direction": { "x": #, "y": # },
                "position": { "x": #, "y": # }
            }
            The vector need not be normalized. Note that the missile may choose to override this direction once fired!

        :return: the new EnemyState
        """
        # State specific to us
        color = enemy_state["pak_specific_state"].get("color")

        if color is None:
            color = random.choice(list(self.get_sprite_details().keys()))
            enemy_state["pak_specific_state"]["color"] = color
            enemy_state["sprite"] = self.sprites[color][random.randint(0, 8)]

        # What size should our sprite be drawn on-screen as?
        enemy_state["sprite_size"]["width"] = 64
        enemy_state["sprite_size"]["height"] = 64

        # What's our hitbox rect (relative to the top-left corner of the sprite)?
        enemy_state["hitbox"]["x"] = 0
        enemy_state["hitbox"]["y"] = 0
        enemy_state["hitbox"]["width"] = 64
        enemy_state["hitbox"]["height"] = 64

        # How are we moving?  And what's our sprite?
        # Flee player, dumb
        player_x = all_states["player"]["position"]["x"]
        player_y = all_states["player"]["position"]["y"]

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
            enemy_state["sprite"] = self.sprites[color][random.randint(0, 8)]

        # Do we want to fire a missile?
        # Fire every 1.5 seconds, aimed at the player
        last_fired = enemy_state["pak_specific_state"].get("last_fired")

        if last_fired is None or time_since_start - last_fired > 1.5:
            new_missiles.append({
                "direction": {
                    "x": player_x - enemy_state["position"]["x"],
                    "y": player_y - enemy_state["position"]["y"]
                },
                "position": enemy_state["position"].copy()
            })
            enemy_state["pak_specific_state"]["last_fired"] = time_since_start

        # How do we interact with the borders of the screen?
        # TODO: make the game engine actually handle this using these variables, instead of doing it here
        enemy_state["wrap_x"] = True
        enemy_state["wrap_y"] = True

        if enemy_state["position"]["x"] < 0:
            enemy_state["position"]["x"] = 0
        if enemy_state["position"]["x"] > 800:
            enemy_state["position"]["x"] = 800
        if enemy_state["position"]["y"] < 0:
            enemy_state["position"]["y"] = 0
        if enemy_state["position"]["y"] > 600:
            enemy_state["position"]["y"] = 600

        # Return the new state
        return enemy_state

    def collided_with_player(self, enemy_state, player_state):
        """
        :param enemy_state: Our state
        :param player_state: PlayerState for who we hit

        Usually, the player is responsible for marking themselves as dead when they hit an enemy.

        Set enemy_state["active"] = False to indicate that we're dying, or player_state["active"] = False to indicate it's dying

        :return: None
        """
        pass

    def collided_with_player_missile(self, enemy_state, missile_state):
        """
        :param enemy_state: Our state
        :param missile_state: PlayerState for who we hit

        Usually, the enemy is responsible for marking themselves as dead when they hit a player missile,
        and the missile is responsible for marking itself as stopped when it hits something.

        Set enemy_state["active"] = False to indicate that we're dying, or missile["active"] = False to indicate it's dying

        :return: None
        """
        enemy_state["active"] = False

    def collided_with_level(self, enemy_state, previous_position):
        """
            Called whenever the player bumps into a wall.
            Usually, you just want to set enemy_state["position"] = previous_position

        :param enemy_state: Our state
        :param previous_position: Where were we before be bumped into the wall?
        :return: the new EnemyState
        """
        enemy_state["position"] = previous_position
        return enemy_state
