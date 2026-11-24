from __future__ import annotations

import re

from app.core.printer_manager import PrinterManager


class SharingError(RuntimeError):
    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


def valid_share_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip()).strip("_")[:80]
    if not cleaned:
        raise ValueError("O nome de compartilhamento não contém caracteres válidos.")
    return cleaned


def suggested_share_name(printer_name: str) -> str:
    return valid_share_name(printer_name)[:64]


def _error_code(exc: Exception) -> int | None:
    code = getattr(exc, "winerror", None)
    if code is None and getattr(exc, "args", ()) and isinstance(exc.args[0], int):
        code = exc.args[0]
    return code


class PrinterSharing:
    def ensure_shared(self, printer_name: str, requested_name: str) -> tuple[str, bool]:
        printer = PrinterManager().find(printer_name)
        if printer is None:
            raise SharingError(f"Impressora não encontrada: {printer_name}")
        if printer.share_name:
            return printer.share_name, False
        share_name = valid_share_name(requested_name)
        try:
            import win32print
            handle = win32print.OpenPrinter(printer_name, {"DesiredAccess": win32print.PRINTER_ALL_ACCESS})
            try:
                info = win32print.GetPrinter(handle, 2)
                info["pShareName"] = share_name
                info["Attributes"] = int(info.get("Attributes") or 0) | win32print.PRINTER_ATTRIBUTE_SHARED
                win32print.SetPrinter(handle, 2, info, 0)
            finally:
                win32print.ClosePrinter(handle)
        except Exception as exc:
            raise SharingError(f"Falha ao compartilhar a impressora: {exc}", _error_code(exc)) from exc
        verified = PrinterManager().find(printer_name)
        if not verified or verified.share_name.casefold() != share_name.casefold():
            raise SharingError("O Windows não confirmou o compartilhamento da impressora.")
        return share_name, True

    def remove_share(self, printer_name: str, expected_share_name: str) -> None:
        """Rollback only the share created by this operation, never an unrelated share."""
        printer = PrinterManager().find(printer_name)
        if not printer or printer.share_name.casefold() != valid_share_name(expected_share_name).casefold():
            return
        try:
            import win32print
            handle = win32print.OpenPrinter(printer_name, {"DesiredAccess": win32print.PRINTER_ALL_ACCESS})
            try:
                info = win32print.GetPrinter(handle, 2)
                info["pShareName"] = None
                info["Attributes"] = int(info.get("Attributes") or 0) & ~win32print.PRINTER_ATTRIBUTE_SHARED
                win32print.SetPrinter(handle, 2, info, 0)
            finally:
                win32print.ClosePrinter(handle)
        except Exception as exc:
            raise SharingError(f"Não foi possível reverter o compartilhamento: {exc}", _error_code(exc)) from exc
