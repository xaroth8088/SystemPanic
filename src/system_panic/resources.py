from pathlib import Path
import os
import sys


def asset_root() -> Path:
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "assets")
    candidates.extend([Path(__file__).resolve().parents[2] / "assets",
                       Path(sys.prefix) / "share/system-panic"])
    return next((path for path in candidates if (path / "images").is_dir()), candidates[0])


def data_root() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "SystemPanic"


def pak_roots() -> tuple[Path, ...]:
    if getattr(sys, "frozen", False):
        content = Path(sys.executable).resolve().parent / "paks"
    else:
        checkout = Path(__file__).resolve().parents[2] / "paks"
        content = checkout if checkout.is_dir() else Path(sys.prefix) / "share/system-panic/paks"
    return content, data_root() / "paks"
