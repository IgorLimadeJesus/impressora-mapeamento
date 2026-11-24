from __future__ import annotations

import getpass
import os

from app.core.permissions import is_admin
from app.core.port_mapper import PortMapper
from app.core.printer_manager import PrinterManager
from app.core.windows_api import computer_name, windows_version


def spooler_status() -> str:
    try:
        import win32serviceutil
        state = win32serviceutil.QueryServiceStatus("Spooler")[1]
        return {1: "Parado", 2: "Iniciando", 3: "Parando", 4: "Em execução", 7: "Pausado"}.get(state, f"Estado {state}")
    except Exception as exc:
        return f"Indisponível: {exc}"


def collect_diagnostics() -> dict:
    try:
        printers = PrinterManager().list_printers()
        printer_error = ""
    except Exception as exc:
        printers, printer_error = [], str(exc)
    try:
        mappings = PortMapper().list_mappings()
        mapping_error = ""
    except Exception as exc:
        mappings, mapping_error = [], str(exc)
    return {
        "Windows": windows_version(), "Computador": computer_name(), "Usuário": getpass.getuser(),
        "Administrador": "Sim" if is_admin() else "Não", "Spooler": spooler_status(),
        "Impressoras": [p.to_dict() for p in printers], "Erro de impressoras": printer_error,
        "Portas USB": sorted({p.port for p in printers if p.is_usb}),
        "Mapeamentos": [m.to_dict() for m in mappings], "Erro de mapeamentos": mapping_error,
        "Processo": os.getpid(),
    }
