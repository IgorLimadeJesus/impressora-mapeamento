from __future__ import annotations

import logging

from app.core.port_mapper import MappingError, PortMapper
from app.core.permissions import is_admin, run_elevated_and_wait
from app.core.printer_sharing import PrinterSharing, SharingError
from app.core.windows_api import computer_name
from app.models.mapping import LptMapping
from app.services.config_service import ConfigService


logger = logging.getLogger(__name__)


class MappingService:
    def __init__(self, config: ConfigService):
        self.config = config
        self.mapper = PortMapper()
        self.sharing = PrinterSharing()

    def create(self, printer_name: str, share_name: str, port: str, persistent: bool, replace: bool = False) -> LptMapping:
        try:
            actual_share, was_created = self.sharing.ensure_shared(printer_name, share_name)
        except SharingError as exc:
            if exc.code != 5 or is_admin():
                raise
            code = run_elevated_and_wait(["--share-printer", printer_name, "--share-name", share_name])
            if code:
                raise SharingError(f"A operação administrativa de compartilhamento falhou (código {code}).", code) from exc
            actual_share, _ = self.sharing.ensure_shared(printer_name, share_name)
            was_created = True
        remote = rf"\\{computer_name()}\{actual_share}"
        try:
            mapping = self.mapper.create(port, remote, persistent, replace)
        except Exception:
            if was_created:
                try:
                    try:
                        self.sharing.remove_share(printer_name, actual_share)
                    except SharingError as rollback_error:
                        if rollback_error.code == 5 and not is_admin():
                            run_elevated_and_wait(["--unshare-printer", printer_name, "--share-name", actual_share])
                        else:
                            raise
                except Exception as rollback_error:
                    logger.exception("Falha no rollback do compartilhamento: %s", rollback_error)
            raise
        mapping.printer_name = printer_name
        mapping.share_name = actual_share
        self._remember(mapping)
        return mapping

    def remove(self, port: str) -> None:
        self.mapper.remove(port)
        saved = [item for item in self.config.data.get("saved_mappings", []) if item.get("port", "").upper() != port.upper().rstrip(":")]
        self.config.update(saved_mappings=saved)

    def saved(self) -> list[LptMapping]:
        return [LptMapping.from_dict(item) for item in self.config.data.get("saved_mappings", [])]

    def reconnect_saved(self) -> list[tuple[LptMapping, str | None]]:
        results = []
        for mapping in self.saved():
            try:
                active = self.mapper.get_connection(mapping.port)
                if not active or active.casefold() != mapping.remote_path.casefold():
                    mapping = self.mapper.create(mapping.port, mapping.remote_path, mapping.persistent, replace=bool(active))
                results.append((mapping, None))
            except Exception as exc:
                results.append((mapping, str(exc)))
        return results

    def _remember(self, mapping: LptMapping) -> None:
        saved = [item for item in self.config.data.get("saved_mappings", []) if item.get("port", "").upper() != mapping.port]
        saved.append(mapping.to_dict())
        self.config.update(saved_mappings=saved)
