from __future__ import annotations

import argparse
import ctypes
import logging
import os

import customtkinter as ctk

from app.services.config_service import ConfigService
from app.services.log_service import setup_logging
from app.ui.main_window import MainWindow
from app.core.printer_sharing import PrinterSharing


def main() -> int:
    parser = argparse.ArgumentParser(description="Redirecionador de impressoras USB para portas LPT")
    parser.add_argument("--tray", action="store_true", help="iniciar minimizado na bandeja")
    parser.add_argument("--share-printer", help=argparse.SUPPRESS)
    parser.add_argument("--unshare-printer", help=argparse.SUPPRESS)
    parser.add_argument("--share-name", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if os.name != "nt":
        raise SystemExit("Este aplicativo requer Windows 10 ou Windows 11.")
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    if args.share_printer:
        if not args.share_name:
            return 2
        PrinterSharing().ensure_shared(args.share_printer, args.share_name)
        return 0
    if args.unshare_printer:
        if not args.share_name:
            return 2
        PrinterSharing().remove_share(args.unshare_printer, args.share_name)
        return 0
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    config = ConfigService()
    log_path = setup_logging(config.data_dir)
    logging.info("Iniciando USB to LPT Mapper")
    app = MainWindow(config, log_path, start_hidden=args.tray)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
