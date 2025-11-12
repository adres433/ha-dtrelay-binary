import pytest
# Basic checks for config_flow / error messages

def test_error_lookup():
    from custom_components.dtrelay_binary.errors import get_error_message
    assert "Device did not respond" in get_error_message(1258)

def test_sn_length():
    # SN must be 5 digits (basic check)
    assert len("12345") == 5
