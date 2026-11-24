from __future__ import annotations

import re

from app.core.windows_api import run_command
from app.models.mapping import LptMapping


class MappingError(RuntimeError):
    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


def normalize_lpt(value: str) -> str:
    port = value.strip().upper().rstrip(":")
    if not re.fullmatch(r"LPT[1-9]", port):
        raise ValueError("A porta deve estar entre LPT1 e LPT9.")
    return port


def validate_unc(value: str) -> str:
    value = value.strip()
    # Conservative allow-list: enough for normal Windows host/share names while
    # rejecting command metacharacters even though commands never use a shell.
    if not re.fullmatch(r"\\\\[A-Za-z0-9._-]+\\[A-Za-z0-9_$ .-]+", value):
        raise ValueError("Caminho de rede inválido. Use \\\\COMPUTADOR\\COMPARTILHAMENTO.")
    if value.endswith((" ", ".")):
        raise ValueError("O compartilhamento não pode terminar em espaço ou ponto.")
    return value


class PortMapper:
    def get_connection(self, port: str) -> str | None:
        local = normalize_lpt(port) + ":"
        try:
            import win32wnet
            return str(win32wnet.WNetGetConnection(local))
        except ImportError as exc:
            raise MappingError("PyWin32 não está instalado.") from exc
        except Exception as exc:
            code = getattr(exc, "winerror", None)
            if code in (2, 2250):  # ERROR_FILE_NOT_FOUND / ERROR_NOT_CONNECTED
                return None
            # pywintypes.error often stores the code as args[0].
            if getattr(exc, "args", ()) and exc.args[0] in (2, 2250):
                return None
            raise MappingError(f"Falha ao consultar {local}: {exc}", code) from exc

    def list_mappings(self) -> list[LptMapping]:
        items: list[LptMapping] = []
        for index in range(1, 10):
            port = f"LPT{index}"
            remote = self.get_connection(port)
            if remote:
                items.append(LptMapping(port=port, remote_path=remote, available=self.is_available(port)))
        return items

    def create(self, port: str, remote_path: str, persistent: bool = True, replace: bool = False) -> LptMapping:
        port = normalize_lpt(port)
        remote_path = validate_unc(remote_path)
        current = self.get_connection(port)
        if current and current.casefold() == remote_path.casefold():
            return LptMapping(port, current, persistent=persistent, available=self.is_available(port))
        if current and not replace:
            raise MappingError(f"{port} já está mapeada para {current}.")
        removed_existing = False
        if current:
            self.remove(port)
            removed_existing = True
        try:
            result = run_command(["net", "use", f"{port}:", remote_path, f"/persistent:{'yes' if persistent else 'no'}"])
            if not result.ok:
                raise MappingError(result.stderr or result.stdout or "NET USE falhou.", result.returncode)
            verified = self.get_connection(port)
            if not verified or verified.casefold() != remote_path.casefold():
                raise MappingError("O comando terminou, mas o Windows não confirmou o mapeamento.")
        except Exception as original:
            if removed_existing and current:
                # Remove a conexão nova/parcial antes de tentar restaurar a anterior.
                try:
                    if self.get_connection(port):
                        run_command(["net", "use", f"{port}:", "/delete", "/y"])
                    rollback = run_command(["net", "use", f"{port}:", current, "/persistent:yes"])
                    restored = self.get_connection(port)
                    if not rollback.ok or not restored or restored.casefold() != current.casefold():
                        raise MappingError(rollback.stderr or rollback.stdout or "Windows não confirmou a restauração.")
                except Exception as rollback_error:
                    raise MappingError(f"{original} O rollback de {port} para {current} também falhou: {rollback_error}") from original
            raise
        return LptMapping(port, verified, persistent=persistent, available=self.is_available(port))

    def remove(self, port: str) -> None:
        port = normalize_lpt(port)
        if not self.get_connection(port):
            return
        result = run_command(["net", "use", f"{port}:", "/delete", "/y"])
        if not result.ok:
            raise MappingError(result.stderr or result.stdout or "Não foi possível remover o mapeamento.", result.returncode)
        if self.get_connection(port):
            raise MappingError(f"O Windows ainda informa que {port} está conectada.")

    def reconnect(self, mapping: LptMapping) -> LptMapping:
        return self.create(mapping.port, mapping.remote_path, mapping.persistent, replace=True)

    def is_available(self, port: str) -> bool:
        remote = self.get_connection(port)
        if not remote:
            return False
        try:
            import win32print
            handle = win32print.OpenPrinter(remote)
            win32print.ClosePrinter(handle)
            return True
        except Exception:
            return False
