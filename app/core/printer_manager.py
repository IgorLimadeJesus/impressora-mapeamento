from __future__ import annotations

from app.models.printer import Printer


class PrinterError(RuntimeError):
    pass


class PrinterManager:
    def list_printers(self) -> list[Printer]:
        try:
            import win32print
            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            rows = win32print.EnumPrinters(flags, None, 2)
        except ImportError as exc:
            raise PrinterError("PyWin32 não está instalado.") from exc
        except Exception as exc:
            raise PrinterError(f"Não foi possível enumerar as impressoras: {exc}") from exc
        printers: list[Printer] = []
        for row in rows:
            printers.append(Printer(
                name=row.get("pPrinterName") or "", driver=row.get("pDriverName") or "",
                port=row.get("pPortName") or "", status=int(row.get("Status") or 0),
                attributes=int(row.get("Attributes") or 0), share_name=row.get("pShareName") or "",
                server_name=row.get("pServerName") or "",
            ))
        return sorted(printers, key=lambda item: item.name.casefold())

    def find(self, name: str) -> Printer | None:
        target = name.casefold()
        return next((p for p in self.list_printers() if p.name.casefold() == target), None)
