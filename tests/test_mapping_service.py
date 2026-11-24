from unittest.mock import Mock

import pytest

from app.models.mapping import LptMapping
from app.core.printer_sharing import SharingError
from app.services.config_service import ConfigService
from app.services.mapping_service import MappingService


def test_create_persists_verified_mapping(tmp_path, monkeypatch):
    config = ConfigService(tmp_path / "config.json")
    service = MappingService(config)
    service.sharing = Mock()
    service.sharing.ensure_shared.return_value = ("ZEBRA", True)
    service.mapper = Mock()
    service.mapper.create.return_value = LptMapping("LPT3", r"\\PC\ZEBRA", available=True)
    monkeypatch.setattr("app.services.mapping_service.computer_name", lambda: "PC")

    result = service.create("Zebra S4M", "ZEBRA", "LPT3", True)

    assert result.printer_name == "Zebra S4M"
    assert config.data["saved_mappings"][0]["port"] == "LPT3"
    service.sharing.remove_share.assert_not_called()


def test_create_rolls_back_new_share_on_mapping_error(tmp_path, monkeypatch):
    service = MappingService(ConfigService(tmp_path / "config.json"))
    service.sharing = Mock()
    service.sharing.ensure_shared.return_value = ("ZEBRA", True)
    service.mapper = Mock()
    service.mapper.create.side_effect = RuntimeError("net use failed")
    monkeypatch.setattr("app.services.mapping_service.computer_name", lambda: "PC")

    with pytest.raises(RuntimeError):
        service.create("Zebra S4M", "ZEBRA", "LPT3", True)

    service.sharing.remove_share.assert_called_once_with("Zebra S4M", "ZEBRA")


def test_access_denied_elevates_only_share_operation(tmp_path, monkeypatch):
    service = MappingService(ConfigService(tmp_path / "config.json"))
    service.sharing = Mock()
    service.sharing.ensure_shared.side_effect = [SharingError("access denied", 5), ("ZEBRA", False)]
    service.mapper = Mock()
    service.mapper.create.return_value = LptMapping("LPT3", r"\\PC\ZEBRA", available=True)
    elevated = Mock(return_value=0)
    monkeypatch.setattr("app.services.mapping_service.is_admin", lambda: False)
    monkeypatch.setattr("app.services.mapping_service.run_elevated_and_wait", elevated)
    monkeypatch.setattr("app.services.mapping_service.computer_name", lambda: "PC")

    service.create("Zebra S4M", "ZEBRA", "LPT3", True)

    elevated.assert_called_once_with(["--share-printer", "Zebra S4M", "--share-name", "ZEBRA"])
    service.mapper.create.assert_called_once_with("LPT3", r"\\PC\ZEBRA", True, False)
