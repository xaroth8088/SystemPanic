"""Generate original audio separately from the game using Stable Audio 3.

Uses the documented Gradio call/SSE API; no runtime dependencies, accounts,
or model downloads are added to the game. Errors are recorded, never disguised.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def request_json(url: str, data: dict | None = None, token: str = ""):
    body = json.dumps(data).encode() if data is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, body, headers)
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def generate(job: dict, endpoint: str, output: Path, token: str = "") -> dict:
    result = request_json(endpoint + "/gradio_api/call/infer", {"data": [
        job["model"], job["prompt"], job["duration"], 8, 1.0, "pingpong", job["seed"]
    ]}, token)
    event_id = result["event_id"]
    url = endpoint + "/gradio_api/call/infer/" + event_id
    event = ""
    headers = {"Authorization": "Bearer " + token} if token else {}
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=240) as stream:
        for raw in stream:
            line = raw.decode().strip()
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                payload = json.loads(line[5:].strip())
                if event == "error":
                    raise RuntimeError(f"Generation service: {payload!r}")
                if event == "complete":
                    file = payload[0]
                    file_url = file.get("url") or endpoint + "/gradio_api/file=" + file["path"]
                    output.parent.mkdir(parents=True, exist_ok=True)
                    with urllib.request.urlopen(file_url, timeout=90) as response:
                        content = response.read()
                    output.write_bytes(content)
                    return dict(job, provider="Stable Audio 3", endpoint=endpoint,
                                sha256=hashlib.sha256(content).hexdigest(),
                                file=str(output.relative_to(ROOT)), status="generated")
    raise RuntimeError("Generation stream ended without a result")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", default="all")
    parser.add_argument("--endpoint", default="https://stabilityai-stable-audio-3.hf.space")
    args = parser.parse_args()
    jobs = json.loads(Path(__file__).with_name("prompts.json").read_text())["jobs"]
    matches = [j for j in jobs if args.job in ("all", j["id"])]
    if not matches:
        parser.error("Unknown job")
    records_path = ROOT / "assets" / "audio" / "generation.json"
    records = json.loads(records_path.read_text()) if records_path.exists() else {}
    token = os.environ.get("HF_TOKEN", "")
    for token_path in (Path.home() / ".cache/huggingface/token", Path.home() / ".huggingface/token"):
        if not token and token_path.is_file():
            token = token_path.read_text().strip()
    failed = False
    for job in matches:
        output = ROOT / "assets" / "audio" / (job["id"] + ".wav")
        if output.exists() and records.get(job["id"], {}).get("status") == "generated":
            print("Already generated:", job["id"], flush=True)
            continue
        print("Generating:", job["id"], flush=True)
        start = time.monotonic()
        try:
            records[job["id"]] = generate(job, args.endpoint.rstrip("/"), output, token)
            print("Saved:", output.name, round(time.monotonic() - start, 1), "seconds", flush=True)
        except Exception as exc:
            records[job["id"]] = dict(job, status="failed", error=str(exc))
            print("Failed:", job["id"], str(exc), flush=True)
            failed = True
        records_path.write_text(json.dumps(records, indent=2) + "\n")
        if failed:
            break  # Do not hammer a quota-limited or unavailable service.
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
