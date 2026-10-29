"""Release safeguards and quick/full selection, independent of game simulation."""
import importlib.util
import hashlib
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("system_panic_test_runner", ROOT / "tools/test.py")
test_runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_runner)


class NamedTest:
    def __init__(self, name):
        self.name = name

    def id(self):
        return self.name

    def countTestCases(self):
        return 1

    def __call__(self, result=None):
        return result


class RegressionSelectionTests(unittest.TestCase):
    def test_direct_script_discovers_all_modules_from_an_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run([sys.executable, str(ROOT / "tools/test.py"), "--list"],
                                       cwd=temporary, capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertNotIn("_FailedTest", completed.stdout, completed.stdout + completed.stderr)
        self.assertIn("test_audio_generation.", completed.stdout)
        self.assertIn("test_run_feedback.", completed.stdout)
        self.assertIn("Selected ", completed.stdout)

    def test_only_exact_matrix_id_is_removed_from_nested_discovery(self):
        ids = [
            "test_world.WorldTests.test_other_world_behavior",
            test_runner.EXHAUSTIVE_TEST,
            "test_other.OtherTests.test_all_component_mixes_update_and_fire_safely",
            "unittest.loader._FailedTest.test_broken_import",
        ]
        suite = unittest.TestSuite([
            NamedTest(ids[0]),
            unittest.TestSuite([NamedTest(ids[1]), unittest.TestSuite([NamedTest(ids[2])])]),
            NamedTest(ids[3]),
        ])
        selected, excluded = test_runner.regression_suite(suite)
        self.assertEqual([test.id() for test in test_runner.iter_tests(selected)], [ids[0], ids[2], ids[3]])
        self.assertEqual(excluded, [test_runner.EXHAUSTIVE_TEST])
        self.assertEqual(selected.countTestCases() + len(excluded), suite.countTestCases())

    def test_renamed_or_missing_exhaustive_test_fails_instead_of_silent_omission(self):
        with self.assertRaisesRegex(ValueError, "found 0"):
            test_runner.regression_suite(unittest.TestSuite([NamedTest("test_world.WorldTests.renamed_matrix")]))

    def test_duplicate_matrix_or_empty_regressions_are_rejected(self):
        matrix = lambda: NamedTest(test_runner.EXHAUSTIVE_TEST)
        with self.assertRaisesRegex(ValueError, "found 2"):
            test_runner.regression_suite(unittest.TestSuite([matrix(), matrix()]))
        with self.assertRaisesRegex(ValueError, "empty regression"):
            test_runner.regression_suite(unittest.TestSuite([matrix()]))

    def test_failed_regressions_return_failure_and_do_not_start_the_matrix(self):
        def fail_regression():
            raise AssertionError("a real regression failed")

        suite = unittest.TestSuite([
            unittest.FunctionTestCase(fail_regression), NamedTest(test_runner.EXHAUSTIVE_TEST),
        ])
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(test_runner.unittest.defaultTestLoader, "discover", return_value=suite), \
                    patch.object(test_runner.subprocess, "run") as matrix, \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                exit_code = test_runner.main(["--full", "--output", temporary])
            report = json.loads((Path(temporary) / "regressions.json").read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 1)
            self.assertFalse(report["passed"])
            self.assertEqual(report["tests_run"], 1)
            self.assertEqual(len(report["failures"]), 1)
            matrix.assert_not_called()

    def test_full_run_uses_parallel_matrix_and_propagates_its_failure(self):
        suite = unittest.TestSuite([
            unittest.FunctionTestCase(lambda: None), NamedTest(test_runner.EXHAUSTIVE_TEST),
        ])
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.CompletedProcess([], returncode=7)
            with patch.object(test_runner.unittest.defaultTestLoader, "discover", return_value=suite), \
                    patch.object(test_runner.subprocess, "run", return_value=completed) as matrix, \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                exit_code = test_runner.main(["--full", "--workers", "3", "--output", temporary])
            report = json.loads((Path(temporary) / "regressions.json").read_text(encoding="utf-8"))
            command = matrix.call_args.args[0]
            self.assertIn(str(ROOT / "tools/verify_matrix.py"), command)
            self.assertEqual(command[command.index("--workers") + 1], "3")
            self.assertEqual(exit_code, 1)
            self.assertEqual(report["matrix_exit_code"], 7)
            self.assertFalse(report["passed"])


class ReleaseSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        helper_spec = importlib.util.spec_from_file_location("system_panic_release_support", ROOT / "tools/release_support.py")
        cls.support = importlib.util.module_from_spec(helper_spec)
        helper_spec.loader.exec_module(cls.support)

    def test_tag_must_match_the_authoritative_project_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text('[project]\nversion = "0.2.3"\n', encoding="utf-8")
            version = self.support.project_version(root)
            self.assertEqual(version, "0.2.3")
            self.support.validate_tag("v0.2.3", version)
            for tag in ("v0.2.2", "0.2.3", "refs/tags/v0.2.3", "v0.2.3-extra", ""):
                with self.subTest(tag=tag), self.assertRaises(ValueError):
                    self.support.validate_tag(tag, version)

    def test_tagged_preflight_rejects_dirty_or_different_commits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text('[project]\nversion = "0.2.3"\n', encoding="utf-8")
            commit = "a" * 40
            with patch.object(self.support, "_git", side_effect=[commit, "", commit]):
                record = self.support.release_preflight("v0.2.3", root)
            self.assertEqual(record["commit"], commit)
            self.assertFalse(record["dirty"])
            for status in (" M pyproject.toml", "?? untracked.txt"):
                with self.subTest(status=status), patch.object(self.support, "_git", side_effect=[commit, status]):
                    with self.assertRaisesRegex(ValueError, "clean"):
                        self.support.release_preflight("v0.2.3", root)
            with patch.object(self.support, "_git", side_effect=[commit, "", "b" * 40]):
                with self.assertRaisesRegex(ValueError, "exactly"):
                    self.support.release_preflight("v0.2.3", root)
            with patch.object(self.support, "_git", side_effect=[None, None]):
                with self.assertRaisesRegex(ValueError, "Git checkout"):
                    self.support.release_preflight("v0.2.3", root)

    def test_inventory_rejects_stale_missing_and_changed_release_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pilot").mkdir()
            data = root / "pilot/pilot.py"
            data.write_text("COMPONENT = OriginalPilot\n", encoding="utf-8")
            (root / "pak.json").write_text('{"id":"release_probe"}', encoding="utf-8")
            (root / "__pycache__").mkdir()
            (root / "__pycache__/ignored.pyc").write_bytes(b"ignored")
            expected = self.support.file_inventory(root)
            self.assertEqual(set(expected), {"pilot/pilot.py", "pak.json"})
            self.assertEqual(expected["pilot/pilot.py"], hashlib.sha256(data.read_bytes()).hexdigest())
            self.support.verify_inventory(root, expected)
            extra = root / "stale.py"
            extra.write_text("obsolete", encoding="utf-8")
            with self.assertRaises(ValueError):
                self.support.verify_inventory(root, expected)
            extra.unlink()
            original = data.read_bytes()
            data.unlink()
            with self.assertRaises(ValueError):
                self.support.verify_inventory(root, expected)
            data.write_bytes(original + b"# tampered\n")
            with self.assertRaises(ValueError):
                self.support.verify_inventory(root, expected)
            data.write_bytes(original)
            self.support.verify_inventory(root, expected)

    def test_cleanup_is_limited_to_descendants_of_the_intended_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            allowed = root / "dist"
            allowed.mkdir()
            nested = allowed / "SystemPanic"
            nested.mkdir()
            (nested / "stale.txt").write_text("old", encoding="utf-8")
            outside = root / "keep"
            outside.mkdir()
            for path in (allowed, outside, allowed / ".." / "keep"):
                with self.subTest(path=str(path)), self.assertRaises(ValueError):
                    self.support.safe_remove_tree(path, allowed)
                self.assertTrue(outside.exists())
                self.assertTrue(allowed.exists())
            self.support.safe_remove_tree(nested, allowed)
            self.assertFalse(nested.exists())
            self.assertTrue(outside.exists())

    def test_checksums_reject_tampering_duplicate_names_and_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = root / "SystemPanic-v0.2.3-windows-x64.zip"
            payload.write_bytes(b"release bytes")
            manifest = root / "SHA256SUMS.txt"
            self.support.write_checksums([payload], manifest)
            expected = {payload.name: hashlib.sha256(payload.read_bytes()).hexdigest()}
            self.assertEqual(self.support.verify_checksums(manifest), expected)
            original_manifest = manifest.read_text(encoding="utf-8")
            payload.write_bytes(b"tampered bytes")
            with self.assertRaises(ValueError):
                self.support.verify_checksums(manifest)
            payload.write_bytes(b"release bytes")
            manifest.write_text(original_manifest + original_manifest, encoding="utf-8")
            with self.assertRaises(ValueError):
                self.support.verify_checksums(manifest)
            for name in ("../outside.zip", "/outside.zip", "nested/file.zip", "nested\\file.zip"):
                with self.subTest(name=name):
                    manifest.write_text(f'{expected[payload.name]}  {name}\n', encoding="utf-8")
                    with self.assertRaises(ValueError):
                        self.support.verify_checksums(manifest)


if __name__ == "__main__":
    unittest.main()
