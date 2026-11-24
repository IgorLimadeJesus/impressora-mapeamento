from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(slots=True)
class LptMapping:
    port: str
    remote_path: str
    printer_name: str = ""
    share_name: str = ""
    persistent: bool = True
    available: bool = False
    created_at: str = ""

    def __post_init__(self) -> None:
        self.port = self.port.upper().rstrip(":")
        if not self.created_at:
            self.created_at = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LptMapping":
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        return cls(**{key: value for key, value in data.items() if key in allowed})
