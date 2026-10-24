"""Local playback only. Generation is deliberately outside the game."""
import pygame

from .resources import asset_root


class Audio:
    def __init__(self, prefs):
        self.available = False
        self.sounds = {}
        self.current = None
        self.last_played = {}
        self.prefs = prefs
        self.root = asset_root() / "audio"
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(24)
            for name in ("shot", "impact", "shuffle", "hurt", "clear", "select"):
                path = self.find(name)
                if path:
                    self.sounds[name] = pygame.mixer.Sound(path)
            self.available = True
            self.set_volumes()
        except (pygame.error, OSError):
            pass

    def find(self, name):
        return next((folder / (name + ext) for folder in (self.root / "production", self.root)
                     for ext in (".ogg", ".wav") if (folder / (name + ext)).is_file()), None)

    def set_volumes(self):
        if self.available:
            pygame.mixer.music.set_volume(self.prefs.music)
            for name, sound in self.sounds.items():
                sound.set_volume(self.prefs.effects * (.30 if name == "shot" else .70))

    def music(self, name):
        if not self.available or self.current == name:
            return
        path = self.find(name)
        if path:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(-1, fade_ms=650)
                self.current = name
            except (pygame.error, OSError):
                pass

    def play(self, name):
        if not self.available or name not in self.sounds:
            return
        now = pygame.time.get_ticks()
        if now - self.last_played.get(name, -1000) < (65 if name == "shot" else 40):
            return
        self.sounds[name].play()
        self.last_played[name] = now
