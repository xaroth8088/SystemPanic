from abc import ABC, abstractmethod
import pygame # For type hinting

class BasePlatform(pygame.sprite.Sprite, ABC):
    """
    Abstract Base Class for individual Platform sprites, if they need custom logic.
    Most platform modules might just define a way to create a group of simple
    pygame.sprite.Sprite instances. If platforms have special behaviors
    (e.g., moving, crumbling), they should inherit from this.

    For simple static platforms, the module usually just needs:
    1. load_platform_assets(module_path) -> dict
    2. create_platforms(screen_width, screen_height, assets) -> pygame.sprite.Group
    """
    @abstractmethod
    def __init__(self, x: int, y: int, image: pygame.Surface, *args, **kwargs):
        """
        Initialize a platform instance.

        Args:
            x (int): X-coordinate.
            y (int): Y-coordinate.
            image (pygame.Surface): The visual representation of the platform.
        """
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        pass

    # Platforms are often static, so an update method might not always be needed.
    # If they can move or change state, an update method would be defined here.
    # def update(self, dt: float, *args, **kwargs):
    #     pass


# The primary interface for a platform *module* is slightly different:
# It's about loading assets and creating a collection of platforms.

@abstractmethod
def load_platform_assets(module_path: str) -> dict:
    """
    Load all assets required by the platform module (e.g., tile images).
    This function must be defined at the module level of a platform module's __init__.py.

    Args:
        module_path (str): The absolute path to this platform module's directory.

    Returns:
        dict: A dictionary containing the loaded assets, typically tile images.
              Example: {'tile_image': surface, 'edge_tile': surface}
    """
    pass

@abstractmethod
def create_platforms(screen_width: int, screen_height: int, assets: dict) -> pygame.sprite.Group:
    """
    Create and return a group of platform sprites for the level.
    This function must be defined at the module level of a platform module's __init__.py.

    Args:
        screen_width (int): The width of the game screen.
        screen_height (int): The height of the game screen.
        assets (dict): The dictionary of assets loaded by load_platform_assets().

    Returns:
        pygame.sprite.Group: A sprite group containing all platform instances.
    """
    pass