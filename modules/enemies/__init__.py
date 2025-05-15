from abc import ABC, abstractmethod
import pygame  # For type hinting


class BaseEnemy(pygame.sprite.Sprite, ABC):
    """
    Abstract Base Class for all Enemy modules.
    Ensures that all enemy modules implement the necessary methods and properties.
    Enemy modules should inherit from this class.
    """

    # --- Constants that concrete classes should ideally define for clarity ---
    # SPRITESHEET_LAYOUT_NOTE = "Define how your spritesheet is laid out."
    # SPRITE_WIDTH = 32
    # SPRITE_HEIGHT = 32

    @staticmethod
    @abstractmethod
    def load_assets(module_path: str) -> dict:
        """
        Load all assets required by the enemy module.

        Args:
            module_path (str): The absolute path to this enemy module's directory.

        Returns:
            dict: A dictionary containing the loaded assets.
                  Example: {'frames': [surface1, surface2,...]}
        """
        pass

    @abstractmethod
    def __init__(
        self, x: int, y: int, assets: dict, player_rect_for_ai: pygame.Rect | None
    ):
        """
        Initialize the enemy instance.

        Args:
            x (int): Initial x-coordinate.
            y (int): Initial y-coordinate.
            assets (dict): The dictionary of assets loaded by load_assets().
            player_rect_for_ai (pygame.Rect | None): The player's current rect for AI purposes,
                                                     or None if player doesn't exist yet.
        """
        super().__init__()
        self.rect = pygame.Rect(x, y, 32, 32)
        self.image = pygame.Surface([32, 32])
        # Concrete classes will set self.image, self.rect, self.health, etc.
        pass

    @abstractmethod
    def update(
        self, platforms: pygame.sprite.Group, player_rect: pygame.Rect | None, dt: float
    ):
        """
        Update the enemy's state (AI, movement, physics, animation).

        Args:
            platforms (pygame.sprite.Group): Group of platform sprites for collision.
            player_rect (pygame.Rect | None): The player's current rect for AI purposes,
                                              or None if player doesn't exist or is hidden.
            dt (float): Delta time in seconds since the last frame.
        """
        pass

    @abstractmethod
    def take_damage(self, amount: int):
        """
        Apply damage to the enemy.

        Args:
            amount (int): The amount of damage to inflict.
        """
        pass

    @abstractmethod
    def is_alive(self) -> bool:
        """
        Check if the enemy is still alive.

        Returns:
            bool: True if alive, False otherwise.
        """
        pass

    # Optional, but common for enemies that deal damage on touch
    def deal_damage_on_contact(self) -> int:
        """
        Returns the amount of damage this enemy deals on contact with the player.
        If the enemy doesn't deal contact damage, it can return 0 or this method
        might not be implemented (check with hasattr).

        Returns:
            int: Damage amount.
        """
        return 0  # Default no contact damage

    def draw(self, surface: pygame.Surface):
        """
        Draw the enemy onto the given surface.
        (Often handled by sprite group draw, but allows custom drawing).
        """
        surface.blit(self.image, self.rect)  # Basic default implementation
