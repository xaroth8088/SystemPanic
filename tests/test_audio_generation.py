"""Development generator boundary checks; no models or network needed."""
from pathlib import Path
import subprocess
import math
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

from tools.assetforge import local

OUTPUT = Path(__file__).resolve().parents[1] / "output"


class AudioGenerationTests(unittest.TestCase):
    def setUp(self):
        OUTPUT.mkdir(exist_ok=True)

    def test_fractional_jobs_use_whole_second_inference_and_keep_full_source(self):
        with tempfile.TemporaryDirectory(dir=OUTPUT) as directory:
            root = Path(directory)
            def backend(command, **kwargs):
                duration = command[command.index("--seconds") + 1]
                # Emulate the pinned backend's supported conditioning: a whole
                # second count. Mastering later trims after removing lead-in.
                self.assertTrue(float(duration).is_integer(), duration)
                with wave.open(command[-1], "wb") as output:
                    output.setparams((2, 2, 44100, 0, "NONE", "not compressed"))
                    output.writeframes(b"\x12\x01\x34\x02" * (int(float(duration)) * 44100))
                return subprocess.CompletedProcess(command, 0)
            with patch.object(local, "PYTHON", Path(sys.executable)), patch.object(local, "TOOLS", root), \
                 patch.object(local.subprocess, "run", side_effect=backend):
                for seconds in (.8, 1, 1.2, 2):
                    with self.subTest(seconds=seconds):
                        path = root / f"clip-{seconds}.wav"
                        local.render("test", "sm-sfx", seconds, 24, path, offline=True)
                        with wave.open(str(path), "rb") as result:
                            self.assertEqual(result.getparams()[:3], (2, 2, 44100))
                            self.assertEqual(result.getnframes(), math.ceil(seconds) * 44100)
                            self.assertEqual(result.readframes(1), b"\x12\x01\x34\x02")

    def test_failed_generation_preserves_existing_asset(self):
        with tempfile.TemporaryDirectory(dir=OUTPUT) as directory:
            root = Path(directory)
            output = root / "existing.wav"
            output.write_bytes(b"original asset")
            with patch.object(local, "PYTHON", Path(sys.executable)), patch.object(local, "TOOLS", root), \
                 patch.object(local.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)):
                with self.assertRaises(RuntimeError):
                    local.render("test", "sm-sfx", .8, 24, output, offline=True)
            self.assertEqual(output.read_bytes(), b"original asset")

    def test_invalid_durations_do_not_start_inference(self):
        with patch.object(local.subprocess, "run") as backend:
            for seconds in (0, -1, float("nan"), float("inf")):
                with self.subTest(seconds=seconds), self.assertRaises(ValueError):
                    local.render("test", "sm-sfx", seconds, 24, "unused.wav", offline=True)
            backend.assert_not_called()
