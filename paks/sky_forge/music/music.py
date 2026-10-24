"""Sky Forge: independently selectable soundtrack."""
from system_panic.pak_api import MusicBase


class SkyForgeMusic(MusicBase):
    def init(self):
        self.score = self.load_asset("music.ogg")

    def track(self, world=None):
        return self.score
