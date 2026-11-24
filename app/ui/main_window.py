from __future__ import annotations

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.core.diagnostics import collect_diagnostics, spooler_status
from app.core.port_mapper import PortMapper
from app.core.printer_manager import PrinterManager
from app.core.raw_printer import RawPrinter
from app.services.config_service import ConfigService
from app.services.mapping_service import MappingService
from app.services.startup_service import set_startup
from app.ui.pages import DashboardPage, DiagnosticsPage, MappingsPage, PrintTestPage, PrintersPage, SettingsPage


logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    def __init__(self, config: ConfigService, log_path: Path, start_hidden: bool = False):
        super().__init__()
        self.config_service = config
        self.log_path = log_path
        self.mapping_service = MappingService(config)
        self.raw_printer = RawPrinter()
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="usb-lpt")
        self.printers = []
        self.mappings = []
        self.tray = None
        self.title("USB to LPT Mapper")
        self.geometry(config.data.get("window_geometry", "1120x720"))
        self.minsize(940, 620)
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self._build_ui()
        self._start_tray()
        self.refresh_all()
        if config.data.get("auto_reconnect", True):
            self.run_async(self.mapping_service.reconnect_saved, lambda _value: self.refresh_all(), silent=True)
        if start_hidden:
            self.withdraw()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        sidebar = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color=("#e7edf4", "#111827"))
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        ctk.CTkLabel(sidebar, text="USB  →  LPT", font=ctk.CTkFont(size=21, weight="bold"), text_color="#3b82f6").pack(anchor="w", padx=22, pady=(26, 28))
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=24, pady=22)
        self.pages = {
            "Dashboard": DashboardPage(self.content),
            "Impressoras": PrintersPage(self.content, self.refresh_all),
            "Mapeamentos": MappingsPage(self.content, self.create_mapping, self.remove_mapping, self.refresh_all),
            "Teste de impressão": PrintTestPage(self.content, self.print_lpt, self.print_direct, self.import_raw),
            "Diagnóstico": DiagnosticsPage(self.content, self.refresh_diagnostics),
            "Configurações": SettingsPage(self.content, self.config_service.data, self.save_settings, self.open_logs),
            "Logs": self._logs_page(self.content),
        }
        for label in self.pages:
            ctk.CTkButton(sidebar, text=label, anchor="w", height=39, corner_radius=7, fg_color="transparent", hover_color=("#d7e2ef", "#1e293b"), command=lambda name=label: self.show_page(name)).pack(fill="x", padx=12, pady=2)
        ctk.CTkLabel(sidebar, text="v1.0.0\nRedirecionamento por usuário", justify="left", text_color=("#64748b", "#64748b")).pack(side="bottom", anchor="w", padx=22, pady=20)
        self.show_page("Dashboard")

    def _logs_page(self, master):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        ctk.CTkLabel(frame, text="Logs", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", pady=(0, 16))
        frame.text = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=12), wrap="none")
        frame.text.pack(fill="both", expand=True)
        return frame

    def show_page(self, name: str) -> None:
        for page in self.pages.values():
            page.pack_forget()
        self.pages[name].pack(fill="both", expand=True)
        if name == "Logs":
            self.refresh_logs()

    def run_async(self, operation, success=None, *, silent=False) -> None:
        future = self.executor.submit(operation)
        def finished():
            if not future.done():
                self.after(80, finished)
                return
            try:
                value = future.result()
                if success:
                    success(value)
            except Exception as exc:
                logger.exception("Operação falhou")
                if not silent:
                    messagebox.showerror("USB to LPT Mapper", str(exc), parent=self)
        self.after(80, finished)

    def refresh_all(self) -> None:
        def read():
            printers = PrinterManager().list_printers()
            mappings = PortMapper().list_mappings()
            return printers, mappings, spooler_status()
        def apply(value):
            self.printers, self.mappings, spooler = value
            self.pages["Dashboard"].update_data(len(self.printers), self.mappings, spooler)
            self.pages["Impressoras"].update_data(self.printers)
            self.pages["Mapeamentos"].set_printers(self.printers)
            self.pages["Mapeamentos"].update_mappings(self.mappings)
            self.pages["Teste de impressão"].set_printers(self.printers)
        self.run_async(read, apply)

    def create_mapping(self, values: dict) -> None:
        if not values["printer"]:
            messagebox.showwarning("Mapeamento", "Selecione uma impressora.", parent=self)
            return
        existing = next((item for item in self.mappings if item.port == values["port"]), None)
        replace = False
        if existing:
            replace = messagebox.askyesno("Substituir mapeamento?", f"{existing.port} está associada a {existing.remote_path}. Deseja substituí-la?", parent=self)
            if not replace:
                return
        operation = lambda: self.mapping_service.create(values["printer"], values["share"], values["port"], values["persistent"], replace)
        def done(mapping):
            messagebox.showinfo("Mapeamento criado", f"{mapping.port} → {mapping.remote_path}\nO Windows confirmou o mapeamento.", parent=self)
            self.refresh_all()
        self.run_async(operation, done)

    def remove_mapping(self, port: str) -> None:
        if not messagebox.askyesno("Remover mapeamento?", f"Deseja remover {port} para o usuário atual?", parent=self):
            return
        self.run_async(lambda: self.mapping_service.remove(port), lambda _value: self.refresh_all())

    def print_lpt(self, port: str, data: bytes) -> None:
        self.run_async(lambda: self.raw_printer.send_lpt(port, data), lambda count: messagebox.showinfo("Teste concluído", f"{count} bytes enviados exclusivamente por {port}.", parent=self))

    def print_direct(self, printer: str, data: bytes) -> None:
        if not printer:
            messagebox.showwarning("Teste direto", "Selecione uma impressora.", parent=self)
            return
        self.run_async(lambda: self.raw_printer.send_direct(printer, data), lambda job: messagebox.showinfo("Teste direto", f"Trabalho RAW {job} enviado à fila da impressora.", parent=self))

    def import_raw(self, page) -> None:
        path = filedialog.askopenfilename(parent=self, title="Importar comandos RAW", filetypes=[("Comandos de impressão", "*.zpl *.epl *.cpcl *.txt *.prn"), ("Todos os arquivos", "*.*")])
        if not path:
            return
        try:
            data = Path(path).read_bytes()
            page.set_content(data)
        except Exception as exc:
            messagebox.showerror("Importação", str(exc), parent=self)

    def refresh_diagnostics(self) -> None:
        self.run_async(collect_diagnostics, lambda value: self.pages["Diagnóstico"].set_text(json.dumps(value, ensure_ascii=False, indent=2)))

    def refresh_logs(self) -> None:
        try:
            value = self.log_path.read_text(encoding="utf-8", errors="replace")[-100_000:]
        except OSError as exc:
            value = str(exc)
        text = self.pages["Logs"].text
        text.configure(state="normal")
        text.delete("1.0", "end")
        text.insert("1.0", value)
        text.configure(state="disabled")
        text.see("end")

    def save_settings(self, auto_reconnect: bool, startup: bool) -> None:
        try:
            set_startup(startup)
            self.config_service.update(auto_reconnect=auto_reconnect, start_with_windows=startup)
            messagebox.showinfo("Configurações", "Configurações salvas para o usuário atual.", parent=self)
        except Exception as exc:
            messagebox.showerror("Configurações", str(exc), parent=self)

    def open_logs(self) -> None:
        os.startfile(self.log_path)

    def hide_to_tray(self) -> None:
        self.config_service.update(window_geometry=self.geometry())
        if self.tray:
            self.withdraw()
        else:
            self.destroy_app()

    def show_window(self) -> None:
        self.after(0, lambda: (self.deiconify(), self.lift(), self.focus_force()))

    def _start_tray(self) -> None:
        try:
            from PIL import Image, ImageDraw
            import pystray
            image = Image.new("RGB", (64, 64), "#111827")
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle((8, 8, 56, 56), radius=10, fill="#2563eb")
            draw.text((14, 22), "LPT", fill="white")
            self.tray = pystray.Icon("usb_lpt_mapper", image, "USB to LPT Mapper", pystray.Menu(
                pystray.MenuItem("Abrir aplicativo", lambda: self.show_window(), default=True),
                pystray.MenuItem("Verificar conexões", lambda: self.after(0, self.refresh_all)),
                pystray.MenuItem("Reconectar mapeamentos", lambda: self.run_async(self.mapping_service.reconnect_saved, lambda _v: self.refresh_all())),
                pystray.MenuItem("Encerrar", lambda: self.after(0, self.destroy_app)),
            ))
            self.tray.run_detached()
        except Exception:
            logger.exception("System tray indisponível")
            self.tray = None

    def destroy_app(self) -> None:
        if self.tray:
            self.tray.stop()
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.destroy()
