from random import randint


class Pak:
    def generate_walls(self):
        """
            Called whenever a new level is started, to generate the walls for the level.

        :return walls: A list of lists of booleans, to indicate where walls are placed.  Like this:
        walls = [
            [
                [ True, False, ... ],
                [ ... ],
            ]
        ]

        ...such that it can be read as walls[y][x] to see if a wall is present at a location.

        The lists can be arbitrary sized, but they'll be forced into a grid.
        To do this, the blocks will be evenly distributed on the Y axis based on len(walls).  For the X-axis, the
        longest row will be used, and all shorter rows will effectively have 'False' appended until they're the same
        width as the longest row.

        The game engine will take care of finding appropriate starting locations for the player and enemies.

        """
        walls = [
            [False for _ in range(0, 20)]
            for _ in range(0, 20)
        ]

        for _ in range(0, randint(0, 30)):
            walls[randint(0, 19)][randint(0, 19)] = True

        return walls
