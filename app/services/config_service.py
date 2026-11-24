from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from threading import RLock


DEFAULTS = {
    "default_lpt": "LPT3", "persistent": True, "auto_reconnect": True,
    "start_with_windows": False, "saved_mappings": [], "window_geometry": "1120x720",
}


class ConfigService:
    def __init__(self, path: Path | None = None):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "USB-LPT-Mapper"
        self.path = path or base / "config.json"
        self._lock = RLock()
        self.data = self.load()

    @property
    def data_dir(self) -> Path:
        return self.path.parent

    def load(self) -> dict:
        with self._lock:
            if not self.path.exists():
                return dict(DEFAULTS)
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                raw = {}
            return {**DEFAULTS, **raw}

    def save(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary = tempfile.mkstemp(prefix="config-", suffix=".tmp", dir=self.path.parent)
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    json.dump(self.data, stream, ensure_ascii=False, indent=2)
                os.replace(temporary, self.path)
            except Exception:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass
                raise

    def update(self, **values) -> None:
        self.data.update(values)
        self.save()
