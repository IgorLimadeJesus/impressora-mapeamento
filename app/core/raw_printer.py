from __future__ import annotations

import os

from app.core.port_mapper import normalize_lpt


class RawPrintError(RuntimeError):
    pass


ZPL_TEST = b"^XA\r\n^FO30,30\r\n^A0N,40,40\r\n^FDTESTE DE IMPRESSAO^FS\r\n^FO30,90\r\n^A0N,25,25\r\n^FDUSB TO LPT MAPPER^FS\r\n^XZ\r\n"


class RawPrinter:
    def send_direct(self, printer_name: str, data: bytes, document_name: str = "USB-LPT Mapper RAW") -> int:
        if not isinstance(data, bytes) or not data:
            raise ValueError("Os dados RAW devem conter ao menos um byte.")
        try:
            import win32print
            handle = win32print.OpenPrinter(printer_name)
            try:
                job = win32print.StartDocPrinter(handle, 1, (document_name, None, "RAW"))
                try:
                    win32print.StartPagePrinter(handle)
                    written = win32print.WritePrinter(handle, data)
                    win32print.EndPagePrinter(handle)
                finally:
                    win32print.EndDocPrinter(handle)
            finally:
                win32print.ClosePrinter(handle)
            if written != len(data):
                raise RawPrintError(f"Foram enviados {written} de {len(data)} bytes.")
            return int(job)
        except RawPrintError:
            raise
        except Exception as exc:
            raise RawPrintError(f"Falha na impressão RAW direta: {exc}") from exc

    def send_lpt(self, port: str, data: bytes) -> int:
        if not isinstance(data, bytes) or not data:
            raise ValueError("Os dados RAW devem conter ao menos um byte.")
        port = normalize_lpt(port)
        path = rf"\\.\{port}"
        try:
            import win32con
            import win32file
            handle = win32file.CreateFile(
                path, win32con.GENERIC_WRITE, 0, None, win32con.OPEN_EXISTING,
                win32con.FILE_ATTRIBUTE_NORMAL, None,
            )
            try:
                _result, written = win32file.WriteFile(handle, data)
                win32file.FlushFileBuffers(handle)
            finally:
                win32file.CloseHandle(handle)
        except Exception as exc:
            code = getattr(exc, "winerror", None)
            raise RawPrintError(f"Falha ao enviar bytes por {port} (erro {code or 'desconhecido'}): {exc}") from exc
        if written != len(data):
            raise RawPrintError(f"Foram enviados {written} de {len(data)} bytes por {port}.")
        return int(written)
