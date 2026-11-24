import customtkinter as ctk


class MappingsPage(ctk.CTkFrame):
    def __init__(self, master, on_create, on_remove, on_refresh):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="Mapeamentos", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", pady=(0, 16))
        form = ctk.CTkFrame(self, corner_radius=12)
        form.pack(fill="x")
        form.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(form, text="Impressora de destino").grid(row=0, column=0, sticky="w", padx=18, pady=(16, 4))
        ctk.CTkLabel(form, text="Porta atual").grid(row=0, column=1, sticky="w", padx=18, pady=(16, 4))
        self.printer = ctk.CTkComboBox(form, values=[""], command=self._selected)
        self.printer.grid(row=1, column=0, sticky="ew", padx=18)
        self.current_port = ctk.CTkEntry(form, state="disabled")
        self.current_port.grid(row=1, column=1, sticky="ew", padx=18)
        ctk.CTkLabel(form, text="Porta LPT desejada").grid(row=2, column=0, sticky="w", padx=18, pady=(12, 4))
        ctk.CTkLabel(form, text="Nome de compartilhamento").grid(row=2, column=1, sticky="w", padx=18, pady=(12, 4))
        self.lpt = ctk.CTkComboBox(form, values=[f"LPT{i}" for i in range(1, 10)])
        self.lpt.set("LPT3")
        self.lpt.grid(row=3, column=0, sticky="ew", padx=18)
        self.share = ctk.CTkEntry(form, placeholder_text="Ex.: ZEBRA_S4M")
        self.share.grid(row=3, column=1, sticky="ew", padx=18)
        self.persistent = ctk.CTkCheckBox(form, text="Manter conexão após reiniciar")
        self.persistent.select()
        self.persistent.grid(row=4, column=0, sticky="w", padx=18, pady=16)
        buttons = ctk.CTkFrame(form, fg_color="transparent")
        buttons.grid(row=4, column=1, sticky="e", padx=18, pady=12)
        ctk.CTkButton(buttons, text="Atualizar", width=100, fg_color="#334155", command=on_refresh).pack(side="left", padx=4)
        ctk.CTkButton(buttons, text="Criar mapeamento", command=lambda: on_create(self.values())).pack(side="left", padx=4)
        self.table = ctk.CTkTextbox(self, height=220, font=ctk.CTkFont(family="Consolas", size=13), wrap="none")
        self.table.pack(fill="both", expand=True, pady=(16, 10))
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x")
        self.remove_port = ctk.CTkComboBox(bottom, values=[f"LPT{i}" for i in range(1, 10)], width=120)
        self.remove_port.set("LPT3")
        self.remove_port.pack(side="left")
        ctk.CTkButton(bottom, text="Remover mapeamento", fg_color="#b91c1c", hover_color="#991b1b", command=lambda: on_remove(self.remove_port.get())).pack(side="left", padx=10)
        self._printers = {}

    def values(self) -> dict:
        return {"printer": self.printer.get(), "port": self.lpt.get(), "share": self.share.get(), "persistent": bool(self.persistent.get())}

    def set_printers(self, printers) -> None:
        self._printers = {item.name: item for item in printers}
        names = list(self._printers) or [""]
        self.printer.configure(values=names)
        if self.printer.get() not in self._printers:
            self.printer.set(names[0])
        self._selected(self.printer.get())

    def _selected(self, name: str) -> None:
        item = self._printers.get(name)
        self.current_port.configure(state="normal")
        self.current_port.delete(0, "end")
        if item:
            self.current_port.insert(0, item.port)
            if not self.share.get():
                safe = "_".join(name.split())[:64]
                self.share.insert(0, safe)
        self.current_port.configure(state="disabled")

    def update_mappings(self, mappings) -> None:
        lines = [f"{'PORTA':8} {'STATUS':14} DESTINO", "─" * 90]
        lines.extend(f"{item.port:8} {('Disponível' if item.available else 'Indisponível'):14} {item.remote_path}" for item in mappings)
        self.table.configure(state="normal")
        self.table.delete("1.0", "end")
        self.table.insert("1.0", "\n".join(lines) if mappings else "Nenhum mapeamento encontrado.")
        self.table.configure(state="disabled")
