from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class Printer:
    name: str
    driver: str = ""
    port: str = ""
    status: int = 0
    attributes: int = 0
    share_name: str = ""
    server_name: str = ""

    @property
    def is_shared(self) -> bool:
        return bool(self.share_name)

    @property
    def is_network(self) -> bool:
        return self.name.startswith("\\\\") or bool(self.server_name)

    @property
    def is_usb(self) -> bool:
        value = f"{self.port} {self.driver}".upper()
        return "USB" in value or "DOT4" in value

    @property
    def status_text(self) -> str:
        if self.status == 0:
            return "Pronta"
        flags = {
            0x00000001: "Pausada", 0x00000002: "Erro", 0x00000008: "Sem papel",
            0x00000080: "Offline", 0x00000200: "Ocupada", 0x00000400: "Imprimindo",
            0x00400000: "Porta indisponível",
        }
        return ", ".join(text for bit, text in flags.items() if self.status & bit) or f"Código {self.status}"

    def to_dict(self) -> dict:
        return asdict(self)
