"""Tests that validate the test infrastructure itself."""
import pytest


def test_network_blocked():
    """Verify network blocking from conftest is active."""
    import urllib.request
    with pytest.raises(OSError, match="Network access blocked"):
        urllib.request.urlopen("https://example.com")
