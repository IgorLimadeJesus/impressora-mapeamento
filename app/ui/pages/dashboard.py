import customtkinter as ctk

from app.ui.components import StatCard


class DashboardPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="Dashboard", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", pady=(0, 20))
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x")
        cards.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.printers = StatCard(cards, "Impressoras instaladas")
        self.mappings = StatCard(cards, "Mapeamentos ativos")
        self.spooler = StatCard(cards, "Serviço de impressão")
        self.connections = StatCard(cards, "Conexões")
        for index, card in enumerate((self.printers, self.mappings, self.spooler, self.connections)):
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 6, 0 if index == 3 else 6))
        info = ctk.CTkFrame(self, corner_radius=12)
        info.pack(fill="both", expand=True, pady=(18, 0))
        ctk.CTkLabel(info, text="USB → compartilhamento Windows → NET USE → porta LPT", font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w", padx=22, pady=(22, 8))
        ctk.CTkLabel(info, text="O aplicativo redireciona uma fila de impressão. Ele não emula hardware paralelo nem instala um driver de kernel.", wraplength=760, justify="left", text_color=("#526071", "#94a3b8")).pack(anchor="w", padx=22)
        self.status = ctk.CTkLabel(info, text="Atualizando…", justify="left", anchor="nw")
        self.status.pack(fill="both", expand=True, padx=22, pady=22)

    def update_data(self, printer_count: int, mappings, spooler: str) -> None:
        active = sum(1 for item in mappings if item.available)
        self.printers.set(str(printer_count))
        self.mappings.set(str(len(mappings)))
        self.spooler.set(spooler)
        self.connections.set("OK" if len(mappings) == active else ("Atenção" if mappings else "Sem mapeamento"))
        self.status.configure(text="\n".join(f"{m.port}: {m.remote_path} — {'disponível' if m.available else 'indisponível'}" for m in mappings) or "Nenhuma porta LPT redirecionada neste usuário.")
