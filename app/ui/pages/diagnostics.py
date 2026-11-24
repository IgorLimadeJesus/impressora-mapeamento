import customtkinter as ctk


class DiagnosticsPage(ctk.CTkFrame):
    def __init__(self, master, on_refresh):
        super().__init__(master, fg_color="transparent")
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(header, text="Diagnóstico", font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Atualizar diagnóstico", command=on_refresh).pack(side="right")
        self.text = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=13), wrap="none")
        self.text.pack(fill="both", expand=True)

    def set_text(self, value: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value)
        self.text.configure(state="disabled")
