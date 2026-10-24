# main.py
import pygame
import random
import os
import importlib.util
import time  # Not used directly, but pygame.time is
import math

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
MODULE_RANDOMIZE_INTERVAL = 5000  # milliseconds
ENEMY_SPAWN_MIN_DISTANCE = 150
# GRAVITY is defined in individual player/enemy modules if they use it

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# --- Game Asset Cache ---
ASSET_CACHE = {}  # Key: module_file_path, Value: dict of assets


# --- Helper Functions ---
def load_module_from_path(module_name, path_to_module_file):
    spec = importlib.util.spec_from_file_location(module_name, path_to_module_file)
    if spec is None:
        print(
            f"Error: Could not load spec for module {module_name} at {path_to_module_file}"
        )
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error executing module {module_name} at {path_to_module_file}: {e}")
        import traceback

        traceback.print_exc()
        return None


def list_module_dirs(base_module_type_path):
    if not os.path.exists(base_module_type_path):
        return []
    return [
        os.path.join(base_module_type_path, d)
        for d in os.listdir(base_module_type_path)
        if os.path.isdir(os.path.join(base_module_type_path, d))
        and not d.startswith("__")
    ]


def load_assets_for_module_class(module_class, module_path_dir):
    if module_path_dir in ASSET_CACHE:
        return ASSET_CACHE[module_path_dir]

    if hasattr(module_class, "load_assets"):
        try:
            assets = module_class.load_assets(module_path_dir)
            ASSET_CACHE[module_path_dir] = assets
            return assets
        except Exception as e:
            print(
                f"Error loading assets for {module_class.__name__} in {module_path_dir}: {e}"
            )
            return {}
    return {}


def load_assets_for_platform_module(platform_module, module_path_dir):
    if module_path_dir in ASSET_CACHE:
        return ASSET_CACHE[module_path_dir]

    if hasattr(platform_module, "load_platform_assets"):
        try:
            assets = platform_module.load_platform_assets(module_path_dir)
            ASSET_CACHE[module_path_dir] = assets
            return assets
        except Exception as e:
            print(f"Error loading assets for platform module {module_path_dir}: {e}")
            return {}
    return {}


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Modular Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.running = True
        self.game_over = False

        self.player_module_dirs = list_module_dirs(
            os.path.join(os.getcwd(), "modules", "players")
        )
        self.enemy_module_dirs = list_module_dirs(
            os.path.join(os.getcwd(), "modules", "enemies")
        )
        self.platform_module_dirs = list_module_dirs(
            os.path.join(os.getcwd(), "modules", "platforms")
        )

        if (
            not self.player_module_dirs
            or not self.enemy_module_dirs
            or not self.platform_module_dirs
        ):
            print(
                "Error: Missing one or more module types (players, enemies, platforms)."
            )
            print(f"Found Players: {self.player_module_dirs}")
            print(f"Found Enemies: {self.enemy_module_dirs}")
            print(f"Found Platforms: {self.platform_module_dirs}")
            self.running = False
            return

        self.active_player_module_path = None
        self.active_enemy_module_path = None
        self.active_platform_module_path = None

        self.PlayerClass = None
        self.EnemyClass = None
        self.platform_creation_func = None
        self.platform_module_assets = None

        self.player = None
        self.enemies = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.all_projectiles = (
            pygame.sprite.Group()
        )  # Central group for all projectiles

        self.score = 0
        self.enemies_to_spawn_count = 1
        self.last_module_randomize_time = pygame.time.get_ticks()

        self.randomize_modules(initial_setup=True)

    def randomize_modules(self, initial_setup=False):
        print("\nRandomizing modules...")
        current_time = pygame.time.get_ticks()
        self.last_module_randomize_time = current_time

        # --- Select Player module ---
        if not self.player_module_dirs:
            print("No player modules found!")
            self.running = False
            return
        new_player_module_path_dir = random.choice(self.player_module_dirs)

        if (
            not initial_setup
            and self.active_player_module_path == new_player_module_path_dir
            and self.player
        ):
            print(
                f"Player module '{os.path.basename(new_player_module_path_dir)}' unchanged. Keeping existing player."
            )
            # Ensure PlayerClass is still valid if it was somehow cleared
            if (
                not self.PlayerClass
            ):  # Should not happen if player instance exists and path is same
                player_module_file = os.path.join(
                    new_player_module_path_dir, "__init__.py"
                )
                player_module = load_module_from_path(
                    "player_module", player_module_file
                )
                if player_module and hasattr(player_module, "Player"):
                    self.PlayerClass = player_module.Player
        else:
            print(
                f"Switching to player module: {os.path.basename(new_player_module_path_dir)}"
            )
            player_module_file = os.path.join(new_player_module_path_dir, "__init__.py")
            player_module = load_module_from_path("player_module", player_module_file)

            if not player_module or not hasattr(player_module, "Player"):
                print(
                    f"Failed to load Player from {new_player_module_path_dir}. Keeping previous or exiting."
                )
                if initial_setup and not self.PlayerClass:
                    self.running = False
                    return
                # If not initial setup and load fails, the old player (if any) and PlayerClass remain.
            else:
                new_PlayerClass = player_module.Player
                player_assets = load_assets_for_module_class(
                    new_PlayerClass, new_player_module_path_dir
                )

                old_pos = (SCREEN_WIDTH // 4, SCREEN_HEIGHT - 100)
                old_health = 100
                # Store generic state that might be transferable
                old_generic_state = {}

                if self.player:
                    old_pos = self.player.rect.topleft
                    if hasattr(self.player, "health"):
                        old_health = self.player.health

                    # Generic state transfer (attempt)
                    for attr in ["vel_x", "vel_y", "current_fuel", "facing_direction"]:
                        if hasattr(self.player, attr):
                            old_generic_state[attr] = getattr(self.player, attr)

                    if hasattr(self.player, "projectiles"):
                        # If player *type* changes, projectiles are likely incompatible. Kill them.
                        for proj in self.player.projectiles:
                            proj.kill()
                        self.all_projectiles.remove(self.player.projectiles.sprites())
                    self.player.kill()  # Kill the old player sprite instance

                self.PlayerClass = new_PlayerClass  # Update the stored PlayerClass
                self.player = self.PlayerClass(old_pos[0], old_pos[1], player_assets)

                if hasattr(self.player, "health"):
                    self.player.health = old_health

                # Apply generic state to the new player instance if attributes exist
                for attr, value in old_generic_state.items():
                    if hasattr(self.player, attr):
                        setattr(self.player, attr, value)

                if hasattr(
                    self.player, "projectiles"
                ):  # New player has its own projectile group
                    self.all_projectiles.add(self.player.projectiles)

                self.active_player_module_path = new_player_module_path_dir

        # --- Select Enemy module ---
        if not self.enemy_module_dirs:
            print("No enemy modules found!")
            self.running = False
            return
        new_enemy_module_path_dir = random.choice(self.enemy_module_dirs)

        if (
            not initial_setup
            and self.active_enemy_module_path == new_enemy_module_path_dir
            and self.EnemyClass
        ):
            print(
                f"Enemy module '{os.path.basename(new_enemy_module_path_dir)}' unchanged. Existing enemies retained."
            )
            # EnemyClass is already set and correct. Assets should be cached.
            # Ensure assets are loaded if they somehow weren't (e.g., cache cleared externally)
            load_assets_for_module_class(self.EnemyClass, new_enemy_module_path_dir)
        else:
            print(
                f"Switching to enemy module: {os.path.basename(new_enemy_module_path_dir)}"
            )
            enemy_module_file = os.path.join(new_enemy_module_path_dir, "__init__.py")
            enemy_module = load_module_from_path("enemy_module", enemy_module_file)

            if not enemy_module or not hasattr(enemy_module, "Enemy"):
                print(
                    f"Failed to load Enemy from {new_enemy_module_path_dir}. Keeping previous or exiting."
                )
                if initial_setup and not self.EnemyClass:
                    self.running = False
                    return
            else:
                new_EnemyClass = enemy_module.Enemy
                enemy_assets = load_assets_for_module_class(
                    new_EnemyClass, new_enemy_module_path_dir
                )

                existing_enemies_data = []
                for enemy in self.enemies:
                    data = {"pos": enemy.rect.topleft}
                    if hasattr(enemy, "health"):
                        data["health"] = enemy.health
                    # Add other generic enemy states if needed (e.g., velocity, facing_direction)
                    for attr in [
                        "vel_x",
                        "vel_y",
                        "facing_direction",
                        "ai_state",
                    ]:  # ai_state might be too specific
                        if hasattr(enemy, attr):
                            data[attr] = getattr(enemy, attr)
                    existing_enemies_data.append(data)
                    enemy.kill()  # Kill old instance, it will be replaced

                self.EnemyClass = new_EnemyClass  # Update the stored EnemyClass
                for data in existing_enemies_data:
                    player_rect_for_ai = self.player.rect if self.player else None
                    new_enemy_instance = self.EnemyClass(
                        data["pos"][0], data["pos"][1], enemy_assets, player_rect_for_ai
                    )

                    if "health" in data and hasattr(new_enemy_instance, "health"):
                        new_enemy_instance.health = data["health"]
                    for attr, value in data.items():
                        if attr not in ["pos", "health"] and hasattr(
                            new_enemy_instance, attr
                        ):
                            setattr(new_enemy_instance, attr, value)
                    self.enemies.add(new_enemy_instance)
                self.active_enemy_module_path = new_enemy_module_path_dir

        # --- Select Platform module ---
        if not self.platform_module_dirs:
            print("No platform modules found!")
            self.running = False
            return
        new_platform_module_path_dir = random.choice(self.platform_module_dirs)

        if (
            not initial_setup
            and self.active_platform_module_path == new_platform_module_path_dir
            and self.platform_creation_func
        ):
            print(
                f"Platform module '{os.path.basename(new_platform_module_path_dir)}' unchanged. Keeping existing platforms."
            )
            # Ensure assets are loaded if they somehow weren't
            if (
                self.platform_module
            ):  # Assuming self.platform_module is the loaded module object
                load_assets_for_platform_module(
                    self.platform_module, new_platform_module_path_dir
                )

        else:
            print(
                f"Switching to platform module: {os.path.basename(new_platform_module_path_dir)}"
            )
            platform_module_file = os.path.join(
                new_platform_module_path_dir, "__init__.py"
            )
            loaded_platform_module = load_module_from_path(
                "platform_module", platform_module_file
            )  # Use a temp var

            if (
                not loaded_platform_module
                or not hasattr(loaded_platform_module, "create_platforms")
                or not hasattr(loaded_platform_module, "load_platform_assets")
            ):
                print(
                    f"Failed to load Platform module from {new_platform_module_path_dir} or it's malformed."
                )
                if initial_setup and not self.platform_creation_func:
                    self.running = False
                    return
            else:
                self.platform_module = (
                    loaded_platform_module  # Store the loaded module itself
                )
                self.platform_creation_func = self.platform_module.create_platforms
                self.platform_module_assets = load_assets_for_platform_module(
                    self.platform_module, new_platform_module_path_dir
                )

                for p in self.platforms:
                    p.kill()  # Kill old platforms
                self.platforms.empty()

                new_platform_sprites = self.platform_creation_func(
                    SCREEN_WIDTH, SCREEN_HEIGHT, self.platform_module_assets
                )
                self.platforms.add(new_platform_sprites)
                self.active_platform_module_path = new_platform_module_path_dir

        if initial_setup and self.player and not self.game_over:
            self.spawn_enemies()  # Spawn enemies only on initial setup if player is ready

        # If player changed, their projectiles might need re-adding to all_projectiles
        # This is handled by the player re-creation logic adding its new group.

        print(
            f"Active Player Module: {os.path.basename(self.active_player_module_path if self.active_player_module_path else 'None')}"
        )
        print(
            f"Active Enemy Module: {os.path.basename(self.active_enemy_module_path if self.active_enemy_module_path else 'None')}"
        )
        print(
            f"Active Platform Module: {os.path.basename(self.active_platform_module_path if self.active_platform_module_path else 'None')}"
        )

    def spawn_enemies(self):
        # ... (spawn_enemies logic remains largely the same)
        # It will use self.EnemyClass which is now correctly updated or kept.
        if not self.EnemyClass or not self.player:
            print("Cannot spawn enemies: EnemyClass or Player not loaded correctly.")
            return

        # Use the assets associated with the current self.active_enemy_module_path
        enemy_assets = ASSET_CACHE.get(self.active_enemy_module_path)
        if not enemy_assets:
            print(
                f"Warning: Assets for active enemy module {self.active_enemy_module_path} not found in cache during spawn. Attempting load."
            )
            # This might happen if the module was unchanged but assets were somehow not loaded initially.
            # The EnemyClass should be set from the active module.
            if self.EnemyClass:  # Check if EnemyClass is available
                enemy_assets = load_assets_for_module_class(
                    self.EnemyClass, self.active_enemy_module_path
                )
            if not enemy_assets:
                print(
                    f"Critical: Failed to get/load assets for {self.active_enemy_module_path}. Cannot spawn enemies."
                )
                return

        num_to_spawn_now = self.enemies_to_spawn_count - len(self.enemies)

        for _ in range(num_to_spawn_now):
            spawn_attempts = 0
            while spawn_attempts < 100:  # Max attempts to prevent infinite loop
                x = random.randint(0, SCREEN_WIDTH - 50)
                y = random.randint(
                    0, SCREEN_HEIGHT // 2
                )  # Spawn in upper half generally

                distance_ok = True
                if self.player:
                    distance = math.hypot(
                        x - self.player.rect.centerx, y - self.player.rect.centery
                    )
                    if distance < ENEMY_SPAWN_MIN_DISTANCE:
                        distance_ok = False

                collision_with_platform = False
                # Approximate enemy size for spawn check; ideally use EnemyClass.rect.size if available before init
                enemy_width_approx = (
                    self.EnemyClass.SPRITE_WIDTH
                    if hasattr(self.EnemyClass, "SPRITE_WIDTH")
                    else 32
                )
                enemy_height_approx = (
                    self.EnemyClass.SPRITE_HEIGHT
                    if hasattr(self.EnemyClass, "SPRITE_HEIGHT")
                    else 32
                )
                spawn_rect = pygame.Rect(x, y, enemy_width_approx, enemy_height_approx)

                for plat in self.platforms:
                    if plat.rect.colliderect(spawn_rect):
                        collision_with_platform = True
                        break

                if distance_ok and not collision_with_platform:
                    new_enemy = self.EnemyClass(
                        x, y, enemy_assets, self.player.rect
                    )  # Pass player_rect for AI
                    self.enemies.add(new_enemy)
                    break
                spawn_attempts += 1
            else:  # while loop finished due to max_attempts
                print(
                    f"Warning: Could not find suitable spawn location for an enemy after {spawn_attempts} attempts."
                )

        print(
            f"Spawned {num_to_spawn_now} new enemies. Total: {len(self.enemies)}. Target: {self.enemies_to_spawn_count}"
        )

    def run(self):
        while self.running:
            current_time = pygame.time.get_ticks()
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if self.game_over and event.key == pygame.K_r:
                        self.restart_game()
                    if (
                        not self.game_over
                        and self.player
                        and hasattr(self.player, "handle_event")
                    ):
                        self.player.handle_event(
                            event
                        )  # For single key presses if player module uses it

            if self.game_over:
                self.draw_game_over()
                pygame.display.flip()
                continue  # Skip rest of game loop

            # --- Module Randomization Timer ---
            if (
                current_time - self.last_module_randomize_time
                > MODULE_RANDOMIZE_INTERVAL
            ):
                self.randomize_modules()

            # --- Updates ---
            keys = pygame.key.get_pressed()
            if self.player:
                self.player.update(
                    keys, self.platforms, dt
                )  # Pass dt for frame-independent movement/physics
                if hasattr(self.player, "projectiles"):  # Manage player's projectiles
                    self.all_projectiles.add(self.player.projectiles.sprites())

            player_rect_for_ai = self.player.rect if self.player else None
            for enemy in self.enemies:
                enemy.update(self.platforms, player_rect_for_ai, dt)  # Pass dt

            self.all_projectiles.update()  # Update all active projectiles

            # --- Collision Detection & Game Logic ---
            if self.player:
                # Player <-> Enemy collision (for damage)
                # False for dokill, means enemy sprite is not killed by spritecollide
                enemy_hit_list = pygame.sprite.spritecollide(
                    self.player, self.enemies, False
                )
                for enemy_hit in enemy_hit_list:
                    if hasattr(self.player, "take_damage") and hasattr(
                        enemy_hit, "deal_damage_on_contact"
                    ):
                        # Check for invulnerability frames on player if implemented
                        self.player.take_damage(enemy_hit.deal_damage_on_contact())

                # Projectile <-> Enemy collision
                for proj in self.all_projectiles:
                    # True for dokill on enemy, False for dokill on projectile (proj kills itself)
                    hit_enemies = pygame.sprite.spritecollide(proj, self.enemies, False)
                    for enemy_hit in hit_enemies:
                        if hasattr(enemy_hit, "take_damage") and hasattr(
                            proj, "damage"
                        ):
                            enemy_hit.take_damage(proj.damage)
                            self.score += 10  # Score for hitting
                            proj.kill()  # Projectile is consumed on hit
                            break  # Projectile can only hit one enemy per frame typically

                if hasattr(self.player, "is_alive") and not self.player.is_alive():
                    self.game_over = True
                    print("Game Over - Player defeated")

            for enemy in list(self.enemies):  # Iterate copy for safe removal
                if hasattr(enemy, "is_alive") and not enemy.is_alive():
                    enemy.kill()
                    self.score += 100

            if (
                not self.enemies and not self.game_over and self.player
            ):  # All enemies defeated this wave
                print("Wave cleared!")
                self.enemies_to_spawn_count += 1
                self.randomize_modules()  # Randomize for next wave
                if (
                    self.running and self.player
                ):  # Ensure game still running and player exists
                    self.spawn_enemies()

            # --- Drawing ---
            self.screen.fill(BLACK)
            self.platforms.draw(self.screen)
            self.enemies.draw(self.screen)
            if self.player:
                self.player.draw(self.screen)  # Player module's own draw method

            self.all_projectiles.draw(self.screen)  # Draw all active projectiles

            # UI
            score_text = self.font.render(f"Score: {self.score}", True, WHITE)
            self.screen.blit(score_text, (10, 10))
            if self.player and hasattr(self.player, "health"):
                health_val = self.player.health if self.player.health > 0 else 0
                health_text = self.font.render(
                    f"Health: {health_val}", True, GREEN if health_val > 30 else RED
                )
                self.screen.blit(health_text, (SCREEN_WIDTH - 150, 10))

            enemies_left_text = self.font.render(
                f"Enemies: {len(self.enemies)}/{self.enemies_to_spawn_count}",
                True,
                WHITE,
            )
            self.screen.blit(enemies_left_text, (10, 40))

            time_to_random = (
                MODULE_RANDOMIZE_INTERVAL
                - (current_time - self.last_module_randomize_time)
            ) // 1000
            random_timer_text = self.font.render(
                f"Shuffle in: {max(0, time_to_random)}s", True, WHITE
            )
            self.screen.blit(
                random_timer_text,
                (SCREEN_WIDTH // 2 - random_timer_text.get_width() // 2, 10),
            )

            pygame.display.flip()

        pygame.quit()

    def draw_game_over(self):
        self.screen.fill(BLACK)
        game_over_text = self.font.render("GAME OVER", True, RED)
        restart_text = self.font.render("Press R to Restart", True, WHITE)
        final_score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)

        self.screen.blit(
            game_over_text,
            (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 3),
        )
        self.screen.blit(
            final_score_text,
            (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT // 2),
        )
        self.screen.blit(
            restart_text,
            (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT * 2 // 3),
        )

    def restart_game(self):
        print("Restarting game...")
        ASSET_CACHE.clear()  # Clear asset cache on full restart
        self.score = 0
        self.enemies_to_spawn_count = 1
        self.game_over = False
        self.last_module_randomize_time = pygame.time.get_ticks()

        if self.player:
            self.player.kill()
            self.player = None
        for group in [self.enemies, self.platforms, self.all_projectiles]:
            for sprite in group:
                sprite.kill()
            group.empty()

        self.randomize_modules(initial_setup=True)


if __name__ == "__main__":
    game = Game()
    if game.running:
        game.run()
    else:
        print("Game initialization failed. Exiting.")
        pygame.quit()
