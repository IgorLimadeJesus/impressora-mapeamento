import customtkinter as ctk


class PrintersPage(ctk.CTkFrame):
    def __init__(self, master, on_refresh):
        super().__init__(master, fg_color="transparent")
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(header, text="Impressoras", font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Atualizar impressoras", command=on_refresh).pack(side="right")
        self.text = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=13), wrap="none")
        self.text.pack(fill="both", expand=True)

    def update_data(self, printers) -> None:
        lines = [f"{'NOME':40}  {'PORTA':18}  {'TIPO':8}  {'STATUS':18}  COMPARTILHAMENTO", "─" * 112]
        for item in printers:
            kind = "Rede" if item.is_network else ("USB" if item.is_usb else "Local")
            lines.append(f"{item.name[:40]:40}  {item.port[:18]:18}  {kind:8}  {item.status_text[:18]:18}  {item.share_name or '—'}")
            lines.append(f"  Driver: {item.driver}")
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines) if printers else "Nenhuma impressora encontrada.")
        self.text.configure(state="disabled")
