from unittest.mock import Mock, call

import pytest

from app.core.port_mapper import MappingError, PortMapper
from app.core.windows_api import CommandResult


def result(code: int, error: str = "") -> CommandResult:
    return CommandResult([], code, "", error)


def test_failed_replacement_restores_previous_mapping(monkeypatch):
    mapper = PortMapper()
    old = r"\\PC\OLD_QUEUE"
    mapper.get_connection = Mock(side_effect=[old, None, old])
    mapper.remove = Mock()
    command = Mock(side_effect=[result(2, "new failed"), result(0)])
    monkeypatch.setattr("app.core.port_mapper.run_command", command)

    with pytest.raises(MappingError, match="new failed"):
        mapper.create("LPT3", r"\\PC\NEW_QUEUE", replace=True)

    mapper.remove.assert_called_once_with("LPT3")
    assert command.call_args_list == [
        call(["net", "use", "LPT3:", r"\\PC\NEW_QUEUE", "/persistent:yes"]),
        call(["net", "use", "LPT3:", old, "/persistent:yes"]),
    ]
