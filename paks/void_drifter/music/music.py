"""Void Drifter: independently selectable soundtrack."""
from system_panic.pak_api import MusicBase


class VoidDrifterMusic(MusicBase):
    def init(self):
        self.score = self.load_asset("music.ogg")

    def track(self, world=None):
        return self.score
