"""Deterministic audio mastering after AI generation. Never called by the game."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    audio = ROOT / "assets/audio"
    records = json.loads((audio / "generation.json").read_text())
    local_records = audio / "local/generation.json"
    if local_records.is_file():
        records.update(json.loads(local_records.read_text()))
    derivatives = []
    production = audio / "production"
    production.mkdir(exist_ok=True)
    # The final public generation job hit quota. Use a short portion of the
    # successfully generated AI completion chime for the menu confirmation.
    select = audio / "select.wav"
    if not select.exists():
        data, sr = sf.read(audio / "clear.wav", always_2d=True)
        energy = np.mean(np.abs(data), axis=1)
        start = max(0, int(np.argmax(energy[:int(sr * .8)])) - int(sr * .04))
        clip = data[start:start + int(sr * .12)]
        sf.write(select, clip, sr, subtype="PCM_16")
    derivatives.append({"file":"assets/audio/select.wav", "source":"assets/audio/clear.wav",
                        "operation":"120ms excerpt around the first chime transient", "sha256":digest(select)})
    sources = {path.stem:path for path in audio.glob("*.wav")}
    sources.update({path.stem:path for path in (audio / "local").glob("*.wav")})
    for path in sorted(sources.values(), key=lambda path: path.stem):
        data, sr = sf.read(path, always_2d=True)
        is_music = path.stem in {job["id"] for job in records.values() if job.get("kind") == "music"}
        peak = max(float(np.abs(data).max()), .001)
        data = data * ((.68 if is_music else .82) / peak)
        if is_music:
            # Rotate a crossfaded overlap to form a smooth cyclic boundary.
            overlap = min(int(sr * .18), len(data) // 10)
            ramp = np.linspace(0, 1, overlap)[:, None]
            seam = data[-overlap:] * (1 - ramp) + data[:overlap] * ramp
            data = np.concatenate([seam, data[overlap:-overlap]])
        else:
            energy = np.max(np.abs(data), axis=1)
            active = np.flatnonzero(energy > .015)
            if len(active):
                start = max(0, int(active[0]) - int(sr * .012))
                end = min(len(data), int(active[-1]) + int(sr * .035))
                data = data[start:end]
            if path.stem == "shot":
                data = data[:int(sr * .24)]
            fade = min(int(sr * .015), len(data) // 4)
            if fade:
                data[:fade] *= np.linspace(0, 1, fade)[:, None]
                data[-fade:] *= np.linspace(1, 0, fade)[:, None]
        print("Mastering", path.stem, flush=True)
        encoder = shutil.which("ffmpeg")
        output = production / (path.stem + (".ogg" if encoder else ".wav"))
        if encoder:
            # libsndfile's long Vorbis writes can overflow the Windows stack.
            # Keep libsndfile to PCM IO and use the installed FFmpeg encoder.
            with tempfile.TemporaryDirectory(dir=ROOT / "output") as temporary:
                mastered = Path(temporary) / "master.wav"
                sf.write(mastered, data, sr, subtype="PCM_16")
                subprocess.run([encoder, "-y", "-v", "error", "-i", str(mastered),
                                "-c:a", "libvorbis", "-q:a", "4", str(output)],
                               check=True, capture_output=True)
        else:
            sf.write(output, data, sr, subtype="PCM_16")
        # Playback prefers OGG; remove only this tool's stale alternate so a
        # later WAV-only mastering run cannot accidentally play an older OGG.
        alternate = output.with_suffix(".wav" if output.suffix == ".ogg" else ".ogg")
        alternate.unlink(missing_ok=True)
        derivatives.append({"file":str(output.relative_to(ROOT)).replace("\\", "/"),
                            "source":str(path.relative_to(ROOT)).replace("\\", "/"),
                            "operation":"peak normalized; music loop crossfade" if is_music else "trimmed, faded and peak normalized",
                            "seconds":round(len(data) / sr, 3), "sample_rate":sr, "sha256":digest(output)})
    (audio / "prepared.json").write_text(json.dumps(derivatives, indent=2) + "\n")
    print("Prepared", len(derivatives), "production audio assets/derivatives")


if __name__ == "__main__":
    main()
