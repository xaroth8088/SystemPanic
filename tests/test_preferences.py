import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from system_panic.preferences import Preferences, PreferenceStore

TEMP_ROOT = Path(__file__).resolve().parents[1] / "output" / "test-temp"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


class PreferenceTests(unittest.TestCase):
    def test_old_arena_and_pilot_locks_migrate_to_six_channels(self):
        prefs = Preferences.from_dict({"shuffle_channels":["pilot", "arena"]})
        self.assertEqual(prefs.shuffle_channels, ["pilot", "music", "background", "obstacles"])
        current = Preferences.from_dict({"schema_version":2, "shuffle_channels":["pilot"]})
        self.assertEqual(current.shuffle_channels, ["pilot"])
        self.assertEqual(current.schema_version, 2)

    def test_malformed_values_are_sanitized(self):
        prefs = Preferences.from_dict({"enabled":["missing", {}, []], "music":float("nan"),
                                       "effects":9, "shuffle_seconds":-5, "high_score":-1,
                                       "fullscreen":"yes", "shuffle_channels":["unknown"],
                                       "difficulty":"impossible", "mix_mode":[]})
        self.assertEqual(prefs.enabled, ["signal_runner"])
        self.assertEqual(prefs.music, .55)
        self.assertEqual(prefs.effects, 1)
        self.assertEqual(prefs.shuffle_seconds, 4)
        self.assertFalse(prefs.fullscreen)
        self.assertEqual(prefs.high_score, 0)
        self.assertEqual(prefs.shuffle_channels, [])
        self.assertEqual(prefs.mix_mode, "remix")

    def test_atomic_round_trip_and_corruption_recovery(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            store = PreferenceStore(Path(temp))
            prefs = Preferences(enabled=["sky_forge"], music=0., high_score=12345, reduced_motion=True)
            self.assertTrue(store.save(prefs))
            self.assertEqual(store.load(), prefs)
            self.assertEqual(list(Path(temp).glob("*.tmp")), [])
            store.path.write_text("{broken")
            self.assertEqual(store.load(), Preferences())
            self.assertTrue(store.error)

    def test_write_failure_is_reported(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            blocker = Path(temp) / "not-a-directory"
            blocker.write_text("occupied")
            store = PreferenceStore(blocker)
            self.assertFalse(store.save(Preferences()))
            self.assertIn("save", store.error)

    def test_old_finite_run_preference_is_ignored_and_removed_on_save(self):
        from system_panic.model import Controls, FIXED_DT
        from system_panic.world import World
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            store = PreferenceStore(Path(temp))
            store.path.write_text(json.dumps({"endless":False, "music":.2, "enabled":["signal_runner"]}))
            prefs = store.load()
            self.assertEqual(prefs.music, .2)
            world = World(prefs, 24)
            world.wave = 8
            world.enemies.clear()
            world.phase = "clear"
            world.phase_timer = 0
            world.step(FIXED_DT, Controls())
            self.assertEqual(world.wave, 9)
            self.assertEqual(world.phase, "active")
            self.assertTrue(store.save(prefs))
            self.assertNotIn("endless", json.loads(store.path.read_text()))
