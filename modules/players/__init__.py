from abc import ABC, abstractmethod
import pygame  # For type hinting if using pygame.sprite.Sprite as base


class BasePlayer(pygame.sprite.Sprite, ABC):
    """
    Abstract Base Class for all Player modules.
    Ensures that all player modules implement the necessary methods and properties.
    Player modules should inherit from this class.
    """

    # --- Constants that concrete classes should ideally define for clarity ---
    # SPRITE_WIDTH = 32  # Example default, override in concrete class
    # SPRITE_HEIGHT = 48 # Example default, override in concrete class

    @staticmethod
    @abstractmethod
    def load_assets(module_path: str) -> dict:
        """
        Load all assets required by the player module (spritesheets, sounds, etc.).
        Should be callable before an instance of the player is created.

        Args:
            module_path (str): The absolute path to this player module's directory.

        Returns:
            dict: A dictionary containing the loaded assets, typically keyed by
                  asset type (e.g., 'spritesheet', 'frames', 'sound_jump').
                  Example: {'frames': [surface1, surface2,...], 'projectile_image': surface}
        """
        pass

    @abstractmethod
    def __init__(self, x: int, y: int, assets: dict):
        """
        Initialize the player instance.

        Args:
            x (int): Initial x-coordinate.
            y (int): Initial y-coordinate.
            assets (dict): The dictionary of assets loaded by load_assets().
        """
        super().__init__()  # Initialize pygame.sprite.Sprite
        self.rect = pygame.Rect(
            x, y, 32, 32
        )  # Placeholder, should be set by concrete class
        self.image = pygame.Surface([32, 32])  # Placeholder
        # Concrete classes will set self.image, self.rect, self.health, etc.
        pass

    @abstractmethod
    def update(
        self,
        keys: pygame.key.ScancodeWrapper,
        platforms: pygame.sprite.Group,
        dt: float,
    ):
        """
        Update the player's state, including movement, physics, and animations.

        Args:
            keys (pygame.key.ScancodeWrapper): Current state of all keyboard keys.
            platforms (pygame.sprite.Group): Group of platform sprites for collision.
            dt (float): Delta time in seconds since the last frame.
        """
        pass

    @abstractmethod
    def take_damage(self, amount: int):
        """
        Apply damage to the player.

        Args:
            amount (int): The amount of damage to inflict.
        """
        pass

    @abstractmethod
    def is_alive(self) -> bool:
        """
        Check if the player is still alive.

        Returns:
            bool: True if alive, False otherwise.
        """
        pass

    @abstractmethod
    def draw(self, surface: pygame.Surface):
        """
        Draw the player onto the given surface.
        Note: If inheriting from pygame.sprite.Sprite and adding to a Group,
        the group's draw() method often suffices, but this allows for custom drawing
        (e.g., health bars, effects).

        Args:
            surface (pygame.Surface): The surface to draw on.
        """
        surface.blit(self.image, self.rect)  # Basic default implementation

    # --- Optional methods that enhance functionality but might not be in all players ---

    def handle_event(self, event: pygame.event.Event):
        """
        Handle specific pygame events (e.g., single key presses for actions).
        This is optional; many player types might only use get_pressed() in update().

        Args:
            event (pygame.event.Event): The pygame event to process.
        """
        pass  # Default implementation does nothing

    # Player modules typically manage their own projectiles if they have them.
    # A 'projectiles' property (pygame.sprite.Group) is common.
    # @property
    # def projectiles(self) -> pygame.sprite.Group:
    #     """
    #     Returns a sprite group of projectiles fired by this player.
    #     If the player doesn't fire projectiles, this can return an empty group
    #     or the property might not be implemented (check with hasattr).
    #     """
    #     return pygame.sprite.Group() # Default empty group
