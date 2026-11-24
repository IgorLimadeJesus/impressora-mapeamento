import customtkinter as ctk


class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, config: dict, on_save, on_open_logs):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="Configurações", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", pady=(0, 16))
        card = ctk.CTkFrame(self, corner_radius=12)
        card.pack(fill="x")
        self.auto = ctk.CTkCheckBox(card, text="Reconectar mapeamentos salvos ao iniciar")
        self.auto.pack(anchor="w", padx=20, pady=(20, 10))
        self.startup = ctk.CTkCheckBox(card, text="Iniciar com o Windows (usuário atual)")
        self.startup.pack(anchor="w", padx=20, pady=10)
        if config.get("auto_reconnect", True): self.auto.select()
        if config.get("start_with_windows", False): self.startup.select()
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(12, 20))
        ctk.CTkButton(row, text="Salvar configurações", command=lambda: on_save(bool(self.auto.get()), bool(self.startup.get()))).pack(side="left")
        ctk.CTkButton(row, text="Abrir arquivo de logs", fg_color="#334155", command=on_open_logs).pack(side="left", padx=8)
        ctk.CTkLabel(self, text="Contexto do Windows", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(24, 8))
        ctk.CTkLabel(self, text="Mapeamentos NET USE pertencem ao usuário e à sessão que os criou. Crie o mapeamento no mesmo usuário do SmartClient/WebAgent. Se a impressão ocorre no AppServer, o mapeamento precisa existir na conta do serviço ou a rotina deve imprimir na estação.", wraplength=820, justify="left").pack(anchor="w")
