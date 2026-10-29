from system_panic.pak_api import MusicBase


class KilnMusic(MusicBase):
    def init(self):
        self.audio = self.load_asset('music.ogg')

    def track(self, world=None):
        return self.audio
