import json

from app.services.config_service import ConfigService


def test_config_defaults_and_atomic_save(tmp_path):
    path = tmp_path / "nested" / "config.json"
    config = ConfigService(path)
    assert config.data["default_lpt"] == "LPT3"
    config.update(auto_reconnect=False, custom="ok")
    assert json.loads(path.read_text(encoding="utf-8"))["custom"] == "ok"
    assert not list(path.parent.glob("*.tmp"))


def test_invalid_json_recovers_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("not-json", encoding="utf-8")
    assert ConfigService(path).data["persistent"] is True
