from pathlib import Path
import sys


def asset_root() -> Path:
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "assets")
    candidates.extend([Path(__file__).resolve().parents[2] / "assets",
                       Path(sys.prefix) / "share/system-panic"])
    return next((path for path in candidates if (path / "images").is_dir()), candidates[0])
