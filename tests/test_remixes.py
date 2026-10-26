import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from system_panic.paks import CHANNELS, get_catalog
from system_panic.paks.registry import Catalog
from system_panic.remixes import Remix, RemixStore, mix_issues, normalize_name, validate_mix

TEMP_ROOT = Path(__file__).resolve().parents[1] / "output" / "test-temp"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


class RemixStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.store = RemixStore(Path(self.temp.name))
        self.mix = {channel: get_catalog().providers(channel)[0] for channel in CHANNELS}

    def tearDown(self):
        self.temp.cleanup()

    def test_named_favorites_create_rename_delete_and_preserve_order(self):
        first = Remix("first", "  First   mix  ", self.mix)
        second = Remix("second", "Second mix", self.mix)
        self.assertTrue(self.store.save([first, second]))
        loaded = self.store.load()
        self.assertEqual([item.id for item in loaded], ["first", "second"])
        self.assertEqual(loaded[0].name, "First mix")
        self.assertEqual(loaded[0].mix, self.mix)
        loaded[0].name = "Renamed"
        self.assertTrue(self.store.save(loaded))
        self.assertEqual(self.store.load()[0].name, "Renamed")
        self.assertTrue(self.store.save(loaded[1:]))
        self.assertEqual([item.id for item in self.store.load()], ["second"])
        self.assertTrue(self.store.save([]))
        self.assertEqual(self.store.load(), [])
        self.assertEqual(list(Path(self.temp.name).glob("*.tmp")), [])

    def test_missing_or_changed_providers_are_retained_but_not_playable(self):
        favorite = Remix("favorite", "My mix", self.mix)
        self.assertTrue(self.store.save([favorite]))
        empty = Catalog((), (), ())
        other_store = RemixStore(Path(self.temp.name), empty)
        self.assertEqual(other_store.load(), [favorite])
        self.assertEqual(len(mix_issues(favorite.mix, empty)), 6)
        with self.assertRaises(ValueError):
            validate_mix(favorite.mix, empty)
        # An installed Pak can also stop supplying a component after an update.
        from dataclasses import replace
        original = get_catalog().paks[0]
        partial = replace(original, parts={"pilot": original.parts["pilot"]})
        changed = Catalog((partial,), (), ())
        self.assertEqual(len(mix_issues(self.mix, changed)), 5)
        self.assertTrue(other_store.save([favorite]))
        self.assertEqual(other_store.load(), [favorite])

    def test_validation_requires_exactly_six_eligible_ids_and_copies_selection(self):
        checked = validate_mix(self.mix)
        self.assertEqual(checked, self.mix)
        self.assertIsNot(checked, self.mix)
        for invalid in (None, [], {}, self.mix | {"unknown": "signal_runner"},
                        self.mix | {"pilot": []}, self.mix | {"pilot": "missing"},
                        self.mix | {"pilot": "../unsafe"}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_mix(invalid)
            self.assertTrue(mix_issues(invalid))

    def test_untrusted_records_are_skipped_without_losing_valid_favorites(self):
        good = {"id": "favorite", "name": "My mix", "mix": self.mix}
        invalid = [None, {}, good | {"id": []}, good | {"name": " "},
                   good | {"mix": {}}, good]
        self.store.path.write_text(json.dumps({"schema_version": 1, "remixes": [good, *invalid]}))
        self.assertEqual(self.store.load(), [Remix("favorite", "My mix", self.mix)])
        self.assertIn("6 invalid", self.store.error)

    def test_corrupt_file_recovers_and_subsequent_success_clears_error(self):
        self.assertEqual(self.store.load(), [])
        self.assertFalse(self.store.error)
        for raw in ("{broken", "[]", '{"schema_version":true,"remixes":[]}',
                    '{"schema_version":2,"remixes":[]}', '{"schema_version":1,"remixes":{}}'):
            self.store.path.write_text(raw)
            self.assertEqual(self.store.load(), [])
            self.assertIn("Could not read", self.store.error)
        self.assertTrue(self.store.save([]))
        self.assertEqual(self.store.load(), [])
        self.assertFalse(self.store.error)

    def test_failed_replace_leaves_previous_favorites_and_cleans_temporary_file(self):
        favorite = Remix("favorite", "My mix", self.mix)
        self.assertTrue(self.store.save([favorite]))
        previous = self.store.path.read_bytes()
        with patch("system_panic.remixes.Path.replace", side_effect=OSError("disk is read-only")):
            self.assertFalse(self.store.save([]))
        self.assertIn("Could not save", self.store.error)
        self.assertEqual(self.store.path.read_bytes(), previous)
        self.assertEqual(list(Path(self.temp.name).glob("*.tmp")), [])
        self.assertEqual(self.store.load(), [favorite])

    def test_invalid_saves_and_non_directory_report_failure_without_replacing_file(self):
        favorite = Remix("favorite", "My mix", self.mix)
        self.assertTrue(self.store.save([favorite]))
        previous = self.store.path.read_bytes()
        for invalid in ([favorite, favorite], [Remix("bad", " ", self.mix)], [None]):
            self.assertFalse(self.store.save(invalid))
            self.assertEqual(self.store.path.read_bytes(), previous)
        blocker = Path(self.temp.name) / "not-a-directory"
        blocker.write_text("occupied")
        self.assertFalse(RemixStore(blocker).save([]))

    def test_names_are_readable_bounded_and_support_unicode_and_many_favorites(self):
        self.assertEqual(normalize_name("  Café\n\t Remix  "), "Café Remix")
        self.assertEqual(normalize_name("x" * 100), "x" * 48)
        for invalid in (None, [], "", " \t\n", "bad\x00name"):
            with self.assertRaises(ValueError):
                normalize_name(invalid)
        favorites = [Remix(f"mix-{index}", f"Mix {index}", self.mix) for index in range(150)]
        self.assertTrue(self.store.save(favorites))
        self.assertEqual(self.store.load(), favorites)
