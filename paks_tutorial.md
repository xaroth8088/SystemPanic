# IMPORTANT NOTE
SystemPanic's engine and API are rapidly changing right now, so some details in this documentation will likely change
faster than the docs do.  When in doubt, follow the QuickStart guide and break our your debugger when needed.

# QuickStart
1. Pick a Pak type

 In `SystemPanic/GamePaks` you'll find directories for each type of Pak that SystemPanic supports.  Pick any of these
 folders and open it.

2. Copy an existing Pak

 Copy one of the folders - anything named "ExampleX" is probably good to start with.  Name the folder whatever you like.

3. Start hacking!

 If there's a .py file, just start changing numbers to see how they affect the game.  If there's a .png file, either
 just edit it in-place, or replace it completely if you like.
 
 For folders with both, you'll want to go into the .py file and tweak the "get_sprite_details()" function to match
 your new image.

4. Run the game

 Your Pak will be automatically picked up and randomly included in the rotation.  Want to focus exclusively on your Pak?
 Move or delete all the other paks in the folder.  (This will be made easier and safer later on...)

# Important Concepts

## Pak Functions
As much as is possible, SystemPanic attempts to follow a [functional](https://en.wikipedia.org/wiki/Functional_programming)
style of programming, as this proves to be exceptionally easy to work with when dynamically loading code.

What does this mean in practice?  It means that your Pak functionality always follows the form:

    previous game state -> your function -> next game state

Everything you could ever want/need to know about the state of the game is given to your functions.  You then make
whatever changes you need to the game state to advance the game, and return your new game state.  There are no hidden
side effects going on, and no 'gotchas'.

Because the entirety of the game state can be fiddled with in your Pak, you're able to do all kinds of crazy things if
you want, and the core game engine will still work fine.

## Pak Images
Images should be in .png format, and can theoretically be any size.  To keep things feeling "retro", the total game
surface will only be 320 x 240 and then scaled up to fit the player's screen.  So, anything high-res will just go to
waste.

Background images are scaled up to fill the entire screen.  Everything else needs to be sliced up.

### The `get_sprite_details()` function

Wherever we need to take a Pak .png and slice it up, you'll need to specify how to slice it in this function.  This
function gets called once when the engine starts up and then never again, so anything you do dynamically will happen
 inside the `advance()` function.
 
This function should return a Python dict, where each key in the dict has an array of rectangles.  What's a rectangle?
It's a dict with the keys `x`, `y`, `width`, and `height`, where `(x, y)` is the pixel position from the top-left of
the .png.

The names of the keys in the dict can be anything you like.  When `advance()` gets called later on, you'll receive an
object with the same keys and arrays, but the rectangles will be replaced with the PyGame Sprite objects that you can
 drop into `"sprite"` for the frame.  See the `advance()` function below for more details on how to do this.

# Important Data Structures

## Sprites

These are things like "players", "enemies", and "missiles".

All sprites share these properties:

* pak.png - an image file that gets sliced up for drawing individual animation frames
* pak.py - a file that defines the logic for the sprite
* `get_sprite_details()` - a function in pak.py that tells the engine how to slice up pak.png
* `advance()` - a function that gets called every game frame, and which is used to change the game's state
* `collided_with_*()` - a series of functions that are called whenever the sprite bumps into another sprite

Inside the game state, each in-game thing (i.e. players, enemies, missiles) will have use same data structure to
 represent the sprite.  It's really just a Python dict with the following keys:

* active - a boolean that says whether the sprite is alive or dead
* sprite - in this context, it means the PyGame Sprite image to use.  Set this to any of the images you sliced up using
    `get_sprite_details()` earlier in order to have that sprite drawn out for the frame.
* pak_specific_state - a dict that you can fill with whatever data you like.  It's good for things like "when did I fire
    last?" or "which color should I be?", etc.
* position: a dict with "x" and "y" keys that say where you are in the world, relative to the top-left of the screen.
    Assume that your screen is 320 x 240 (the engine does the scaling from this itself)
* sprite_size: a dict with "width" and "height" keys that say how big the sprite should be drawn.
* target: One of "enemy" or "player", usually only useful for missiles to help differentiate who they're going to damage
* hitbox: A rectangle relative to the top-left of the sprite.  When this rectangle intersects with another sprite's
    rectangle, they'll each get a callback to let them know about it.
* facing: A vector (a Python dict with "x" and "y" for keys) to say which way the sprite's facing.
* start_time: In game time, when was this sprite instantiated?  Useful for calculating animation frames or determining
    if your missile's life is now over.
* wrap_x, wrap_y: booleans to tell the engine what to do when the sprite hits the edge of the screen.  Set to True for
    Pac-Man physics

More is planned here, specifically around standard physics properties so that it's easier to apply a physics engine
where desired.

## `game_state`

Everything you need to know about the current state of the game.  Pak functions will receive one of these, and are
generally expected to return a new game_state that reflects whatever changes the Pak wants to make.

# Important Functions

## `advance(sprites, path, game_state, time_since_start, delta_t, new_missiles)`

This is the heart of the Pak, and is where all the magic happens in the game!

It will receive a game_state object which can be modified to your heart's content as long as the basic structure
remains intact.  At the end of your Pak's `advance()`, be sure to return the new game_state object!

In the future, the engine will attempt to make this safer to work with, to prevent accidental
programming errors from the paks.

Here's what the params do:

* sprites - This is the object filled with sprites that was defined back in `get_sprite_details()`.
* path - A tuple of (key, index) that tells you how to find yourself inside of game_state (see below for example)
* game_state - The entire game state from the start of this frame.  Make whatever changes you like to it, then return
    the game_state at the end of `advance()`.
* time_since_start - in milliseconds, how long has it been since the game started?  Useful for picking animation frames.
* delta_t - in milliseconds, how long has passed since we were last called?  Whenever you're trying to decide how to
    move your sprite, be sure to scale it according to this value - otherwise, the movement of your sprite will be
    dependent on the performance of the machine running the game, which is almost certainly not what you actually want
* new_missiles - a list, which you can append to if you want to add more missiles.  Use `new_missiles.append(<missile>)` to
    add your missile, where `<missile>` has the following structure:
    * target - one of "enemy" or "player", to indicate who this should damage
    * position - the starting position of the missile
    * direction - the starting direction vector of the missile.  The engine will normalize this, so you don't have to do
        extra math here.

To get at the state for yourself, do something like:

```python
    key, index = path
    my_state = game_state[key][index]
```

### Example: picking an animation frame

Let's say that you've set up your `get_sprite_details()` object like this:

```python
    {
        "left": [
            <rectangle for frame 1>,
            <rectangle for frame 2>,
            <rectangle for frame 3>,
            <rectangle for frame 4>
        ],
        "right": [
            <rectangle for frame 1>,
            <rectangle for frame 2>,
            <rectangle for frame 3>,
            <rectangle for frame 4>
        ]
    }
```

When `advance()` gets called, you'll get an object with the same shape, except the rectangles will be replaced with
sprite objects.

So, let's use `time_since_start` to determine which animation frame to use, and `direction` to pick whether we're
facing left or right.  Once we've picked our frame, we'll store it in `game_state` so that it's drawn out to the screen.

```python
    def advance(sprites, path, game_state, time_since_start, delta_t, new_missiles):
        # We probably only want to modify this specific sprite, so let's go find ourselves...
        key, index = path
        my_state = game_state[key][index]
    
        # Pick whether we're facing left or right based on the sprite direction
        direction = "left"
        if my_state["direction"]["x"] > 0:
            direction = "right"
        
        # Every 250ms, advance the frame
        frame_number = ( time_since_start // 250 ) % 4
        
        # Pull out the animation frame from the sprites object
        frame = sprites[direction][frame_number]
        
        # Set it for our state
        # Note that this works because my_state will be a pointer into the spot in game_state (and not its own object)
        my_state["sprite"] = frame
        
        # Whatever else we're doing in advance()
        # ...
        
        # Return the new state
        return game_state
```
