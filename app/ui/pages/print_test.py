import customtkinter as ctk

from app.core.raw_printer import ZPL_TEST


class PrintTestPage(ctk.CTkFrame):
    def __init__(self, master, on_lpt, on_direct, on_import):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="Teste de impressão RAW", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(self, text="Os bytes são enviados sem conversão. O teste pela LPT valida o caminho usado pelo sistema legado.", text_color=("#526071", "#94a3b8")).pack(anchor="w", pady=(0, 12))
        tools = ctk.CTkFrame(self, fg_color="transparent")
        tools.pack(fill="x", pady=(0, 10))
        self.lpt = ctk.CTkComboBox(tools, values=[f"LPT{i}" for i in range(1, 10)], width=110)
        self.lpt.set("LPT3")
        self.lpt.pack(side="left")
        self.printer = ctk.CTkComboBox(tools, values=[""], width=300)
        self.printer.pack(side="left", padx=8)
        ctk.CTkButton(tools, text="Importar arquivo", fg_color="#334155", command=lambda: on_import(self)).pack(side="right")
        self.editor = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=14), wrap="none")
        self.editor.pack(fill="both", expand=True)
        self.editor.insert("1.0", ZPL_TEST.decode("ascii"))
        self._raw_bytes = None
        self._encoding = "utf-8"
        self.editor.bind("<KeyPress>", self._mark_edited, add="+")
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(actions, text="Testar pela porta LPT", command=lambda: on_lpt(self.lpt.get(), self.bytes())).pack(side="left")
        ctk.CTkButton(actions, text="Teste direto (diagnóstico)", fg_color="#334155", command=lambda: on_direct(self.printer.get(), self.bytes())).pack(side="left", padx=8)
        self.result = ctk.CTkLabel(actions, text="", anchor="e")
        self.result.pack(side="right")

    def bytes(self) -> bytes:
        if self._raw_bytes is not None:
            return self._raw_bytes
        try:
            return self.editor.get("1.0", "end-1c").encode(self._encoding)
        except UnicodeEncodeError as exc:
            raise ValueError(f"O texto contém caracteres incompatíveis com {self._encoding}: {exc}") from exc

    def set_printers(self, printers) -> None:
        names = [item.name for item in printers] or [""]
        self.printer.configure(values=names)
        if self.printer.get() not in names:
            self.printer.set(names[0])

    def set_content(self, data: bytes) -> None:
        try:
            text = data.decode("utf-8")
            self._encoding = "utf-8"
        except UnicodeDecodeError:
            text = data.decode("latin-1")
            self._encoding = "latin-1"
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self._raw_bytes = data
        self.result.configure(text=f"{len(data)} bytes importados sem alteração ({self._encoding})")

    def _mark_edited(self, _event=None) -> None:
        if self._raw_bytes is not None:
            self._raw_bytes = None
            self.result.configure(text=f"Conteúdo editado; será codificado em {self._encoding}")
