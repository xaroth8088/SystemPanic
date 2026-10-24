"""Record checked-in asset provenance and validate every production file."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    image_jobs = json.loads(Path(__file__).with_name("image-prompts.json").read_text())
    generation = json.loads((ROOT / "assets/audio/generation.json").read_text())
    prepared = json.loads((ROOT / "assets/audio/prepared.json").read_text())
    local_path = ROOT / "assets/audio/local/generation.json"
    local_generation = json.loads(local_path.read_text()) if local_path.is_file() else {}
    entries = []
    for job in image_jobs["jobs"]:
        path = ROOT / job["file"]
        entries.append(dict(job, provider=image_jobs["provider"], status="generated",
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    entries.extend(job for job in generation.values() if job["status"] == "generated")
    entries.extend(job for job in local_generation.values() if job["status"] == "generated")
    entries.extend(dict(job, status="derived") for job in prepared)
    exports = ROOT / "assets/pak-exports.json"
    if exports.is_file():
        entries.extend(dict(job, status="derived") for job in json.loads(exports.read_text()))
    manifest = {"created":"2026-10-24", "runtime_generation":False,
                "notes":["All revival artwork and audio originate from AI generation for this project.",
                         "Initial cloud outputs are retained. When local outputs exist, production mastering prefers them.",
                         "The original cloud menu-click fallback is retained as a documented derivative; local select supersedes it for production.",
                         "Historical assets under legacy are not used or packaged.",
                         "Music is peak-normalized, crossfaded into loops and encoded as Vorbis outside the runtime."],
                "assets":entries}
    for entry in entries:
        path = ROOT / entry["file"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("Missing or changed asset: " + entry["file"])
    (ROOT / "assets/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Verified provenance for", len(entries), "asset sources and derivatives")


if __name__ == "__main__":
    main()
