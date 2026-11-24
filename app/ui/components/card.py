import customtkinter as ctk


class StatCard(ctk.CTkFrame):
    def __init__(self, master, title: str, value: str = "—", **kwargs):
        super().__init__(master, corner_radius=12, **kwargs)
        ctk.CTkLabel(self, text=title, text_color=("#526071", "#94a3b8"), font=ctk.CTkFont(size=13)).pack(anchor="w", padx=18, pady=(16, 4))
        self.value_label = ctk.CTkLabel(self, text=value, font=ctk.CTkFont(size=25, weight="bold"))
        self.value_label.pack(anchor="w", padx=18, pady=(0, 16))

    def set(self, value: str) -> None:
        self.value_label.configure(text=value)
