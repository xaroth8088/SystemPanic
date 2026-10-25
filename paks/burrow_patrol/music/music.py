"""Burrow Patrol: independent original soundtrack."""
from system_panic.pak_api import MusicBase
class BurrowPatrolMusic(MusicBase):
    def init(self): self.track_asset=self.load_asset("music.ogg")
    def track(self,world=None): return self.track_asset
