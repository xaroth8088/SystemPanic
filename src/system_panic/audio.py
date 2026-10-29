"""Local playback only. Generation is deliberately outside the game."""
import pygame

from .resources import asset_root
from .paks import get_catalog
from .pak_assets import SoundAsset


class Audio:
    def __init__(self, prefs, catalog=None):
        self.catalog = catalog if catalog is not None else get_catalog()
        self.available = False
        self.sounds = {}
        self.current = None
        self.last_played = {}
        self.asset_sounds = {}
        self.common_assets = {}
        self.voices = {}
        self.prefs = prefs
        self.root = asset_root() / "audio"
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(24)
            for name in ("shot", "impact", "shuffle", "hurt", "clear", "select", "game_over"):
                path = self.find(name)
                if path:
                    self.sounds[name] = pygame.mixer.Sound(path)
                    self.common_assets[name] = SoundAsset(path, self)
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
            for index, (asset, volume, loop) in self.voices.items():
                pygame.mixer.Channel(index).set_volume(self.prefs.effects * volume)

    def music(self, track):
        path = track.path if track else None
        if not self.available or self.current == path:
            return
        pygame.mixer.music.stop()
        self.current = path
        if path:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(-1, fade_ms=650)
            except (pygame.error, OSError):
                pass

    def play_asset(self, asset, *, loop=False, volume=1.):
        if not self.available:
            return
        for index in tuple(self.voices):
            if not pygame.mixer.Channel(index).get_busy():
                del self.voices[index]
        if loop and any(owner is asset and looping for owner, _, looping in self.voices.values()):
            return
        try:
            if asset.path not in self.asset_sounds:
                self.asset_sounds[asset.path] = pygame.mixer.Sound(asset.path)
            for index in range(pygame.mixer.get_num_channels()):
                channel = pygame.mixer.Channel(index)
                if not channel.get_busy():
                    self.voices[index] = (asset, volume, loop)
                    channel.set_volume(self.prefs.effects * volume)
                    channel.play(self.asset_sounds[asset.path], loops=-1 if loop else 0)
                    return
        except (pygame.error, OSError):
            pass

    def stop_asset(self, asset):
        for index, (owner, _, _) in tuple(self.voices.items()):
            if owner is asset:
                if self.available:
                    pygame.mixer.Channel(index).stop()
                del self.voices[index]

    def stop_effects(self):
        if self.available:
            pygame.mixer.stop()
        self.voices.clear()

    def play(self, name):
        if not self.available or name not in self.sounds:
            return
        now = pygame.time.get_ticks()
        if now - self.last_played.get(name, -1000) < (65 if name == "shot" else 40):
            return
        self.common_assets[name].play(volume=.30 if name == "shot" else .70)
        self.last_played[name] = now
