import pytest

from app.core.port_mapper import normalize_lpt, validate_unc
from app.core.printer_sharing import valid_share_name
from app.models.printer import Printer


@pytest.mark.parametrize("source, expected", [("lpt3", "LPT3"), ("LPT9:", "LPT9")])
def test_normalize_lpt(source, expected):
    assert normalize_lpt(source) == expected


@pytest.mark.parametrize("value", ["LPT0", "LPT10", "COM1", "LPT3 & whoami"])
def test_reject_invalid_lpt(value):
    with pytest.raises(ValueError):
        normalize_lpt(value)


def test_unc_validation_blocks_command_characters():
    assert validate_unc(r"\\PC-01\ZEBRA_S4M") == r"\\PC-01\ZEBRA_S4M"
    for value in [r"C:\printer", r"\\PC\share & calc", r"\\PC\bad|name", r"\\PC"]:
        with pytest.raises(ValueError):
            validate_unc(value)


def test_share_name_is_sanitized():
    assert valid_share_name("Zebra S4M (USB)") == "Zebra_S4M_USB"


def test_usb_detection():
    assert Printer("Zebra", port="USB001").is_usb
    assert Printer("Laser", driver="DOT4 driver").is_usb
    assert not Printer("PDF", port="PORTPROMPT:").is_usb
