"""Independent local streamed loop; track selection never consumes RNG."""
from system_panic.pak_api import MusicBase


class Music(MusicBase):
    def init(self):
        self.audio = self.load_asset("music.ogg")

    def track(self, world=None):
        return self.audio
